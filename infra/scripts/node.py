#!/usr/bin/env python3
"""Managed node operations. Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later."""

import argparse
import configparser
import datetime
import fcntl
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

CONFIG = Path("/etc/bato")
DATA = Path("/srv/bato/postgres")
RELEASES = Path("/opt/bato/releases")
CURRENT = Path("/opt/bato/current")
SECRET_OWNERS = {
    "db-password": 999,
    "api-password": 999,
    "api-pgpass": 10001,
    "pgbackrest.conf": 999,
    "dns-token": 0,
    "monitor.curl": 0,
}


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def capture(*args):
    return subprocess.check_output(args, text=True).strip()


def atomic(path, data, mode=0o600, uid=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        os.fchmod(fd, mode)
        os.fchown(fd, uid, uid)
        with os.fdopen(fd, "w") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def manifest():
    return json.loads((CONFIG / "node.json").read_text())


def validate_manifest(m):
    for key in ("tenant", "environment"):
        if not re.fullmatch("[a-z][a-z0-9-]{1,30}", m[key]):
            raise ValueError("Invalid node identity")
    if m["environment"] not in ("dev", "prod"):
        raise ValueError("Invalid environment")
    if m["location"] not in ("fsn1", "nbg1") or m["backup_location"] not in ("fsn1", "nbg1"):
        raise ValueError("Node and backups must remain in Germany")
    if m["location"] == m["backup_location"]:
        raise ValueError("Backups require the other German location")
    if not re.fullmatch("[a-f0-9]{40}", m["source_commit"]):
        raise ValueError("An explicitly approved full source commit is required")
    if m["volume_name"] != f"{m['tenant']}-{m['environment']}-postgres":
        raise ValueError("Wrong tenant disk")
    if m["device"] != f"/dev/disk/by-id/scsi-0HC_Volume_{int(m['volume_id'])}":
        raise ValueError("Wrong provider device")
    if not re.fullmatch("[a-z0-9][a-z0-9.-]+", m["node_fqdn"]):
        raise ValueError("Invalid FQDN")
    if not re.fullmatch(r"[^@ \n]+@[^@ \n]+\.[^@ \n]+", m["acme_email"]):
        raise ValueError("Invalid ACME contact")
    for key in ("admin_cidrs", "tenant_cidrs"):
        networks = [ipaddress.ip_network(c) for c in m[key]]
        if {n.version for n in networks} != {4, 6} or any(n.prefixlen == 0 for n in networks):
            raise ValueError("Both IP families require restricted allowlists")


def render(m):
    validate_manifest(m)
    CONFIG.mkdir(mode=0o755, exist_ok=True)
    atomic(CONFIG / "node.json", json.dumps(m, indent=2) + "\n")
    proxy = CONFIG / "proxy"
    proxy.mkdir(mode=0o755, exist_ok=True)
    static = {
        "entryPoints": {"https": {"address": ":443"}},
        "providers": {"file": {"filename": "/etc/traefik/routes.json"}},
        "certificatesResolvers": {
            "dns": {
                "acme": {
                    "email": m["acme_email"],
                    "storage": "/acme/acme.json",
                    "dnsChallenge": {"provider": "hetzner"},
                }
            }
        },
        "api": {"dashboard": False},
        "log": {"level": "WARN"},
    }
    routes = {
        "http": {
            "routers": {
                "bato": {
                    "rule": f"Host(`{m['node_fqdn']}`)",
                    "entryPoints": ["https"],
                    "service": "bato",
                    "tls": {"certResolver": "dns"},
                }
            },
            "services": {"bato": {"loadBalancer": {"servers": [{"url": "http://127.0.0.1:8000"}]}}},
        }
    }
    atomic(proxy / "traefik.json", json.dumps(static))
    atomic(proxy / "routes.json", json.dumps(routes))
    lines = [
        "table inet bato {",
        " chain input { type filter hook input priority -10; policy drop;",
        "  iifname lo accept",
        "  ct state established,related accept",
        "  meta l4proto { icmp, ipv6-icmp } accept",
    ]
    for key, port in (("admin_cidrs", 22), ("tenant_cidrs", 443)):
        for version, family in ((4, "ip"), (6, "ip6")):
            values = [c for c in m[key] if ipaddress.ip_network(c).version == version]
            lines.append(f"  {family} saddr {{ {', '.join(values)} }} tcp dport {port} accept")
    lines.extend(
        [
            " }",
            " chain forward { type filter hook forward priority -10; policy accept;",
            "  ct state established,related accept",
            '  iifname "docker0" accept',
            '  iifname "br-*" accept',
            '  oifname "docker0" drop',
            '  oifname "br-*" drop',
            " }",
            "}",
        ]
    )
    atomic(CONFIG / "firewall.nft", "\n".join(lines) + "\n")


def inject(bundle):
    if set(bundle) != {
        "db_password",
        "api_password",
        "pgbackrest_conf",
        "dns_token",
        "monitor_curl",
    }:
        raise ValueError("Incomplete or unknown secret bundle")
    if any(not isinstance(v, str) or not v or "\0" in v for v in bundle.values()):
        raise ValueError("Empty or invalid secret")
    for key in ("db_password", "api_password", "dns_token"):
        if "\n" in bundle[key] or "\r" in bundle[key]:
            raise ValueError("Passwords and tokens must be single-line values")
    pg = configparser.ConfigParser(interpolation=None)
    pg.read_string(bundle["pgbackrest_conf"])
    if set(pg.sections()) != {"global", "bato"}:
        raise ValueError("Only one explicitly configured backup stanza is allowed")
    required = {
        "repo1-cipher-type": "aes-256-cbc",
        "repo1-storage-verify-tls": "y",
        "expire-auto": "n",
        "archive-async": "n",
        "repo1-retention-full-type": "time",
    }
    if any(pg["global"].get(k) != v for k, v in required.items()):
        raise ValueError("Unsafe backup configuration")
    if int(pg["global"]["repo1-retention-full"]) < 35:
        raise ValueError("Preserve the 30-day boundary full and WAL chain")
    if "archive-push-queue-max" in pg["global"] or "repo1-retention-archive" in pg["global"]:
        raise ValueError("Never drop queued WAL or shorten the retained archive chain")
    if pg["global"].get("repo1-retention-archive-type") != "full":
        raise ValueError("Archive retention must follow complete full backup chains")
    m = manifest()
    if pg["global"]["repo1-path"] != f"/{m['tenant']}/{m['environment']}/epoch-1":
        raise ValueError("Wrong backup repository identity")
    for key, expected in {
        "repo1-type": "s3",
        "repo1-s3-uri-style": "path",
        "repo1-s3-endpoint": f"{m['backup_location']}.your-objectstorage.com",
        "repo1-s3-region": m["backup_location"],
        "repo1-s3-bucket": m["backup_bucket"],
    }.items():
        if pg["global"].get(key) != expected:
            raise ValueError("Backup endpoint/bucket does not match the approved environment")
    escaped = bundle["api_password"].replace("\\", "\\\\").replace(":", "\\:")
    values = {
        "db-password": bundle["db_password"],
        "api-password": bundle["api_password"],
        "api-pgpass": f"db:5432:bato:bato_api:{escaped}\n",
        "pgbackrest.conf": bundle["pgbackrest_conf"],
        "dns-token": bundle["dns_token"],
        "monitor.curl": bundle["monitor_curl"],
    }
    parent = CONFIG / "secrets"
    parent.mkdir(mode=0o711, exist_ok=True)
    directory = parent / uuid.uuid4().hex
    directory.mkdir(mode=0o711)
    for name, value in values.items():
        atomic(directory / name, value, 0o400, SECRET_OWNERS[name])
    link = parent / "next"
    link.symlink_to(directory.name)
    os.replace(link, parent / "current")


def disk_identity(m):
    if not DATA.is_mount():
        raise ValueError("PostgreSQL disk is not mounted")
    device = Path(m["device"]).resolve(strict=True)
    mounted = Path(capture("findmnt", "-n", "-o", "SOURCE", "--target", str(DATA))).resolve()
    if device != mounted:
        raise ValueError("Mounted disk is not the approved retained volume")
    marker = json.loads((DATA / ".bato-volume.json").read_text())
    expected = {k: m[k] for k in ("tenant", "environment", "volume_id")}
    if marker != expected:
        raise ValueError("Retained disk marker does not match this environment")


def gate(initial=False):
    m = manifest()
    validate_manifest(m)
    disk_identity(m)
    if capture("git", "-C", str(CURRENT), "rev-parse", "HEAD") != m["source_commit"]:
        raise ValueError("Runtime source does not match the approved commit")
    if capture("git", "-C", str(CURRENT), "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Runtime source has unapproved modifications")
    verify_images(m["source_commit"])
    for name, uid in SECRET_OWNERS.items():
        path = CONFIG / "secrets/current" / name
        metadata = path.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != uid
            or stat.S_IMODE(metadata.st_mode) != 0o400
            or not metadata.st_size
        ):
            raise ValueError("Required service secret has unsafe ownership or mode")
    if not initial and (DATA / "pgdata/PG_VERSION").read_text().strip() != "16":
        raise ValueError("Existing PG16 data required; initialization is explicit only")
    if not (Path("/var/lib/bato/acme")).is_dir():
        raise ValueError("Private ACME storage missing")


def compose(*args, release=None, **kwargs):
    m = manifest()
    root = release or CURRENT
    env = dict(
        os.environ, BATO_SOURCE_COMMIT=root.resolve().name if release else m["source_commit"]
    )
    return run(
        "docker",
        "compose",
        "--project-name",
        "bato-managed",
        "--project-directory",
        str(root),
        "-f",
        str(root / "compose.yaml"),
        "-f",
        str(root / "deploy/managed/compose.yaml"),
        *args,
        env=env,
        **kwargs,
    )


def install_disk(initialize):
    m = manifest()
    device = Path(m["device"]).resolve(strict=True)
    if not stat.S_ISBLK(device.stat().st_mode):
        raise ValueError("Expected an attached block device")
    DATA.mkdir(parents=True, exist_ok=True)
    if initialize:
        if capture("lsblk", "-n", "-o", "MOUNTPOINTS", str(device)):
            raise ValueError("Refusing to initialize a mounted disk")
        result = subprocess.run(
            ["blkid", "-p", str(device)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 2:
            raise ValueError("Refusing to format a disk with an existing signature")
        run("mkfs.ext4", "-q", str(device))
    unit = f"""[Unit]
Before=bato-node.service
[Mount]
What={m["device"]}
Where={DATA}
Type=ext4
Options=defaults,nodev,nosuid
[Install]
WantedBy=multi-user.target
"""
    atomic(Path("/etc/systemd/system/srv-bato-postgres.mount"), unit, 0o644)
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "--now", "srv-bato-postgres.mount")
    if initialize:
        marker = {k: m[k] for k in ("tenant", "environment", "volume_id")}
        atomic(DATA / ".bato-volume.json", json.dumps(marker))
    disk_identity(m)


def stage(source, approved):
    if not re.fullmatch("[a-f0-9]{40}", approved):
        raise ValueError("Explicit approval must name the full source SHA")
    if capture("git", "-C", source, "rev-parse", "HEAD") != approved:
        raise ValueError("Source checkout does not match approval")
    if capture("git", "-C", source, "status", "--porcelain"):
        raise ValueError("Source checkout must be clean")
    target = RELEASES / approved
    if target.exists():
        raise ValueError("Release already exists; never overwrite staged releases")
    RELEASES.mkdir(parents=True, exist_ok=True)
    run("git", "clone", "--no-hardlinks", "--no-checkout", source, str(target))
    run("git", "-C", str(target), "checkout", "--detach", approved)
    compose("build", "--pull", release=target)
    compose("pull", "proxy", release=target)
    images = {
        name: capture(
            "docker", "image", "inspect", "--format", "{{.Id}}", f"bato-{name}:{approved}"
        )
        for name in ("api", "postgres")
    }
    atomic(CONFIG / "releases" / f"{approved}.json", json.dumps(images))


def verify_images(approved):
    images = json.loads((CONFIG / "releases" / f"{approved}.json").read_text())
    for name in ("api", "postgres"):
        actual = capture(
            "docker", "image", "inspect", "--format", "{{.Id}}", f"bato-{name}:{approved}"
        )
        if actual != images[name]:
            raise ValueError("Staged image changed; do not activate")


def activate(approved, compatible):
    m = manifest()
    target = RELEASES / approved
    if not re.fullmatch("[a-f0-9]{40}", approved) or not target.is_dir():
        raise ValueError("Stage the explicitly approved release first")
    if capture("git", "-C", str(target), "rev-parse", "HEAD") != approved:
        raise ValueError("Invalid staged source")
    verify_images(approved)
    if CURRENT.exists():
        if not compatible:
            raise ValueError("Stop: review schema compatibility or restore to replacement storage")
        gate()
        compose("exec", "-T", "-u", "postgres", "db", "pgbackrest", "--stanza=bato", "check")
        compose(
            "exec",
            "-T",
            "-u",
            "postgres",
            "db",
            "pgbackrest",
            "--stanza=bato",
            "--type=full",
            "backup",
        )
        run("systemctl", "stop", "bato-node")
        previous = CURRENT.resolve()
        atomic(CONFIG / "previous-release", previous.name + "\n")
        history = CONFIG / "history" / previous.name
        history.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONFIG / "node.json", history / "node.json")
        shutil.copytree(CONFIG / "proxy", history / "proxy", dirs_exist_ok=True)
    m["source_commit"] = approved
    render(m)
    link = CURRENT.parent / "next"
    link.symlink_to(target)
    os.replace(link, CURRENT)


def firewall(policy=None):
    existing = subprocess.run(
        ["nft", "list", "table", "inet", "bato"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    prefix = "flush table inet bato\n" if existing.returncode == 0 else ""
    run("nft", "-f", "-", input=prefix + (policy or CONFIG / "firewall.nft").read_text(), text=True)


def backup():
    gate()
    kind = "full" if datetime.datetime.now(datetime.UTC).weekday() == 6 else "diff"
    compose(
        "exec",
        "-T",
        "-u",
        "postgres",
        "db",
        "pgbackrest",
        "--stanza=bato",
        f"--type={kind}",
        "backup",
    )


def monitor():
    gate()
    compose(
        "exec",
        "-T",
        "-u",
        "postgres",
        "db",
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-d",
        "bato",
        "-c",
        "CREATE TABLE IF NOT EXISTS public.bato_operator_heartbeat(at timestamptz NOT NULL); "
        "TRUNCATE public.bato_operator_heartbeat; "
        "INSERT INTO public.bato_operator_heartbeat VALUES (clock_timestamp());",
    )
    compose(
        "exec",
        "-T",
        "-u",
        "postgres",
        "db",
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-d",
        "bato",
        "-c",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_stat_archiver "
        "WHERE last_archived_time IS NULL OR last_archived_time < now()-interval '15 minutes' "
        "OR last_failed_time > last_archived_time) THEN "
        "RAISE EXCEPTION 'archive lag'; END IF; END $$;",
    )
    compose("exec", "-T", "-u", "postgres", "db", "pgbackrest", "--stanza=bato", "check")
    info = json.loads(
        compose(
            "exec",
            "-T",
            "-u",
            "postgres",
            "db",
            "pgbackrest",
            "--stanza=bato",
            "--output=json",
            "info",
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
    )
    latest = max(item["timestamp"]["stop"] for item in info[0]["backup"])
    if datetime.datetime.now(datetime.UTC).timestamp() - latest > 26 * 3600:
        raise ValueError("Physical backup is older than 26 hours")
    usage = shutil.disk_usage(DATA)
    if usage.used / usage.total >= 0.8:
        raise ValueError("Data disk usage exceeds 80 percent")
    with socket.create_connection(("127.0.0.1", 443), timeout=10) as connection:
        with ssl.create_default_context().wrap_socket(
            connection, server_hostname=manifest()["node_fqdn"]
        ) as tls:
            expires = ssl.cert_time_to_seconds(tls.getpeercert()["notAfter"])
            if expires - datetime.datetime.now(datetime.UTC).timestamp() < 21 * 86400:
                raise ValueError("HTTPS certificate expires within 21 days")
    run(
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--max-time",
        "20",
        "--config",
        str(CONFIG / "secrets/current/monitor.curl"),
        stdout=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "render",
            "inject",
            "mount",
            "first-disk",
            "gate",
            "stage",
            "activate",
            "initialize",
            "start",
            "stop",
            "backup",
            "monitor",
            "firewall",
            "rotate-db",
        ],
    )
    parser.add_argument("--source")
    parser.add_argument("--approved-commit")
    parser.add_argument("--schema-compatible", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise ValueError("Run as the authorized root operator")
    if args.command not in ("gate", "start", "stop", "firewall"):
        lock = open("/run/lock/bato-node.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.command == "render":
        render(json.load(sys.stdin))
    elif args.command == "inject":
        inject(json.load(sys.stdin))
    elif args.command in ("mount", "first-disk"):
        install_disk(args.command == "first-disk")
    elif args.command == "stage":
        stage(args.source, args.approved_commit)
    elif args.command == "activate":
        activate(args.approved_commit, args.schema_compatible)
    elif args.command == "initialize":
        if (DATA / "pgdata").exists():
            raise ValueError("Initialization refuses existing PGDATA")
        gate(initial=True)
        compose("up", "-d", "--no-build", "--wait", "db")
        if (DATA / "pgdata/PG_VERSION").read_text().strip() != "16":
            raise ValueError("Initialization failed")
        compose(
            "exec", "-T", "-u", "postgres", "db", "pgbackrest", "--stanza=bato", "stanza-create"
        )
        compose(
            "exec",
            "-T",
            "-u",
            "postgres",
            "db",
            "pgbackrest",
            "--stanza=bato",
            "--type=full",
            "backup",
        )
        compose("stop")
    elif args.command == "start":
        gate()
        compose("up", "-d", "--no-build", "--force-recreate", "--wait")
    elif args.command == "rotate-db":
        gate()
        run("systemctl", "stop", "bato-node")
        compose("up", "-d", "--no-build", "--force-recreate", "--wait", "db")
        try:
            compose(
                "exec",
                "-T",
                "-u",
                "postgres",
                "db",
                "psql",
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "postgres",
                "-d",
                "bato",
                "-f",
                "/run/bato/rotate-credentials.sql",
            )
        finally:
            compose("stop")
    elif args.command == "stop":
        compose("stop")
    elif args.command == "backup":
        backup()
    elif args.command == "monitor":
        monitor()
    elif args.command == "firewall":
        firewall()
    else:
        gate()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, configparser.Error):
        sys.exit(
            "Managed node operation refused; inspect the EU-local configuration and service state."
        )
