#!/usr/bin/env python3
"""Independent state service. Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later."""

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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import node  # noqa: E402

CONFIG = Path("/etc/bato-state")
DATA = Path("/srv/bato-state")


def identity():
    config = json.loads((CONFIG / "identity.json").read_text())
    if not re.fullmatch(r"/dev/disk/by-id/scsi-0HC_Volume_[0-9]+", config["device"]):
        raise ValueError("Expected an approved independent state device")
    if not re.fullmatch("[a-z][a-z0-9.-]+", config["hostname"]):
        raise ValueError("Expected the certificate's state hostname")
    cidrs = [ipaddress.ip_network(c) for c in config["admin_cidrs"]]
    if {c.version for c in cidrs} != {4, 6} or any(c.prefixlen == 0 for c in cidrs):
        raise ValueError("Restrict operator SSH for both address families")
    return config


def compose(*args):
    return node.run(
        "docker",
        "compose",
        "--project-name",
        "bato-state",
        "-f",
        str(CONFIG / "compose.json"),
        *args,
    )


def gate():
    config = identity()
    if config["location"] not in ("fsn1", "nbg1") or config["backup_location"] not in (
        "fsn1",
        "nbg1",
    ):
        raise ValueError("State and backups must remain in Germany")
    if config["location"] == config["backup_location"]:
        raise ValueError("State backups must use the other German location")
    if not DATA.is_mount():
        raise ValueError("Encrypted state filesystem is not mounted")
    source = Path(node.capture("findmnt", "-n", "-o", "SOURCE", "--target", str(DATA))).resolve()
    if source != Path("/dev/mapper/bato-state").resolve(strict=True):
        raise ValueError("Wrong state mount")
    status = node.capture("cryptsetup", "status", "bato-state")
    if "LUKS2" not in status or len(Path("/proc/swaps").read_text().splitlines()) != 1:
        raise ValueError("State requires LUKS2 and disabled swap")
    device_line = next(
        line.split(":", 1)[1].strip()
        for line in status.splitlines()
        if line.strip().startswith("device:")
    )
    if Path(device_line).resolve() != Path(config["device"]).resolve(strict=True):
        raise ValueError("Wrong LUKS backing disk")
    if json.loads((DATA / ".identity").read_text()) != config:
        raise ValueError("Wrong state disk identity")
    for name in ("db-password", "server.key", "server.crt", "ca.crt", "pgbackrest.conf"):
        info = (CONFIG / "secrets" / name).stat()
        if info.st_uid != 999 or stat.S_IMODE(info.st_mode) != 0o400 or not info.st_size:
            raise ValueError("State secret missing or unsafe")


def configure(bundle, source):
    if set(bundle) != {
        "identity",
        "db_password",
        "tls_key",
        "tls_cert",
        "tls_ca",
        "pgbackrest_conf",
        "source_commit",
        "monitor_curl",
    }:
        raise ValueError("Incomplete state bundle")
    sha = bundle["source_commit"]
    backup = configparser.ConfigParser(interpolation=None)
    backup.read_string(bundle["pgbackrest_conf"])
    if set(backup.sections()) != {"global", "state"}:
        raise ValueError("Only the independent state stanza is allowed")
    for key, expected in {
        "repo1-cipher-type": "aes-256-cbc",
        "repo1-storage-verify-tls": "y",
        "expire-auto": "n",
        "archive-async": "n",
        "repo1-path": "/state/epoch-1",
        "repo1-retention-full-type": "time",
    }.items():
        if backup["global"].get(key) != expected:
            raise ValueError("Unsafe state repository configuration")
    if int(backup["global"]["repo1-retention-full"]) < 35 or "state" not in backup:
        raise ValueError("Preserve the state boundary full/WAL chain")
    if any(k in backup["global"] for k in ("archive-push-queue-max", "repo1-retention-archive")):
        raise ValueError("Never drop WAL or shorten state archive retention")
    if backup["global"].get("repo1-retention-archive-type") != "full":
        raise ValueError("State WAL retention must follow full backup chains")
    if not re.fullmatch("[a-f0-9]{40}", sha):
        raise ValueError("Approve full source SHA")
    if node.capture("git", "-C", source, "rev-parse", "HEAD") != sha:
        raise ValueError("Unapproved state bootstrap source")
    if node.capture("git", "-C", source, "status", "--porcelain"):
        raise ValueError("Modified state bootstrap source")
    CONFIG.mkdir(mode=0o700, exist_ok=True)
    node.atomic(CONFIG / "identity.json", json.dumps(bundle["identity"]))
    config = identity()
    for key, expected in {
        "repo1-type": "s3",
        "repo1-s3-uri-style": "path",
        "repo1-s3-endpoint": f"{config['backup_location']}.your-objectstorage.com",
        "repo1-s3-region": config["backup_location"],
        "repo1-s3-bucket": config["backup_bucket"],
    }.items():
        if backup["global"].get(key) != expected:
            raise ValueError("State repository does not match the approved bucket/location")
    rules = [
        "table inet bato {",
        " chain input { type filter hook input priority -10; policy drop;",
        "  iifname lo accept",
        "  ct state established,related accept",
        "  meta l4proto { icmp, ipv6-icmp } accept",
    ]
    for version, family in ((4, "ip"), (6, "ip6")):
        values = [c for c in config["admin_cidrs"] if ipaddress.ip_network(c).version == version]
        rules.append(f"  {family} saddr {{ {', '.join(values)} }} tcp dport 22 accept")
    rules.extend(
        [
            " }",
            " chain forward { type filter hook forward priority -10; policy accept;",
            "  ct state established,related accept",
            '  iifname "br-*" accept',
            '  oifname "br-*" drop',
            " }",
            "}",
        ]
    )
    node.atomic(CONFIG / "firewall.nft", "\n".join(rules) + "\n")
    node.atomic(CONFIG / "monitor.curl", bundle["monitor_curl"], 0o400)
    secrets = CONFIG / "secrets"
    secrets.mkdir(mode=0o711, exist_ok=True)
    values = {
        "db-password": bundle["db_password"],
        "server.key": bundle["tls_key"],
        "server.crt": bundle["tls_cert"],
        "ca.crt": bundle["tls_ca"],
        "pgbackrest.conf": bundle["pgbackrest_conf"],
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value:
            raise ValueError("Missing state key material")
        node.atomic(secrets / name, value, 0o400, 999)
    node.run(
        "docker",
        "build",
        "-f",
        str(Path(source) / "deploy/managed/postgres.Dockerfile"),
        "-t",
        f"bato-state-postgres:{sha}",
        source,
    )
    volumes = [
        {
            "type": "bind",
            "source": str(DATA),
            "target": "/var/lib/postgresql/data",
            "bind": {"create_host_path": False},
        },
        {
            "type": "bind",
            "source": str(secrets),
            "target": "/run/state",
            "read_only": True,
            "bind": {"create_host_path": False},
        },
        {
            "type": "bind",
            "source": str(secrets / "pgbackrest.conf"),
            "target": "/etc/pgbackrest/pgbackrest.conf",
            "read_only": True,
            "bind": {"create_host_path": False},
        },
    ]
    command = [
        "postgres",
        "-c",
        "ssl=on",
        "-c",
        "ssl_cert_file=/run/state/server.crt",
        "-c",
        "ssl_key_file=/run/state/server.key",
        "-c",
        "ssl_ca_file=/run/state/ca.crt",
        "-c",
        "ssl_min_protocol_version=TLSv1.2",
        "-c",
        "archive_mode=on",
        "-c",
        "wal_level=replica",
        "-c",
        "archive_timeout=300s",
        "-c",
        "archive_command=pgbackrest --stanza=state archive-push %p",
        "-c",
        "hba_file=/run/state/pg_hba.conf",
        "-c",
        "password_encryption=scram-sha-256",
        "-c",
        "temp_tablespaces=",
    ]
    node.atomic(
        secrets / "pg_hba.conf",
        "local all postgres trust\nhostssl all all 0.0.0.0/0 scram-sha-256\n"
        "hostssl all all ::/0 scram-sha-256\n",
        0o400,
        999,
    )
    config = {
        "services": {
            "postgres": {
                "image": f"bato-state-postgres:{sha}",
                "restart": "no",
                "volumes": volumes,
                "ports": ["127.0.0.1:5432:5432"],
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "postgres",
                    "POSTGRES_PASSWORD_FILE": "/run/state/db-password",
                    "PGDATA": "/var/lib/postgresql/data/pgdata",
                },
                "command": command,
                "healthcheck": {
                    "test": ["CMD", "pg_isready", "-U", "postgres"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 30,
                },
                "logging": {"driver": "local", "options": {"max-size": "10m", "max-file": "3"}},
            }
        }
    }
    node.atomic(CONFIG / "compose.json", json.dumps(config))


def unlock(first):
    config = identity()
    device = config["device"]
    key = sys.stdin.buffer.read()
    if len(key) < 32:
        raise ValueError("A strong independently escrowed LUKS key is required")
    if first:
        result = subprocess.run(
            ["blkid", "-p", device],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 2:
            raise ValueError("Refusing to initialize a disk with a signature")
        node.run(
            "cryptsetup",
            "luksFormat",
            "--type",
            "luks2",
            "--batch-mode",
            "--key-file",
            "-",
            device,
            input=key,
        )
    node.run("cryptsetup", "open", "--key-file", "-", device, "bato-state", input=key)
    if first:
        node.run("mkfs.ext4", "-q", "/dev/mapper/bato-state")
    DATA.mkdir(parents=True, exist_ok=True)
    node.run("mount", "-o", "nodev,nosuid", "/dev/mapper/bato-state", str(DATA))
    if first:
        node.atomic(DATA / ".identity", json.dumps(config))
    gate()


def pg(*args, **kwargs):
    return node.run(
        "docker",
        "compose",
        "--project-name",
        "bato-state",
        "-f",
        str(CONFIG / "compose.json"),
        "exec",
        "-T",
        "-u",
        "postgres",
        "postgres",
        *args,
        **kwargs,
    )


def database(bundle):
    name = bundle["database"]
    if not re.fullmatch("[a-z][a-z0-9_]{2,60}", name):
        raise ValueError("Use a tenant_environment database and login")
    password = bundle["password"]
    if not isinstance(password, str) or len(password) < 24:
        raise ValueError("Use a strong independent backend password")
    secret = CONFIG / "secrets/role-password"
    node.atomic(secret, password, 0o400, 999)
    sql = (
        "DO $$ BEGIN EXECUTE format("
        f"""'CREATE ROLE "{name}" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', """
        "pg_read_file('/run/state/role-password')); END $$;\n"
        f'CREATE DATABASE "{name}" OWNER "{name}";\n'
        f'REVOKE ALL ON DATABASE "{name}" FROM PUBLIC;\n'
    )
    try:
        pg(
            "psql",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "postgres",
            input=sql.encode(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        secret.unlink()
    pg(
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-d",
        name,
        input=b"REVOKE CREATE ON SCHEMA public FROM PUBLIC;\n",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def monitor():
    gate()
    pg(
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-c",
        "CREATE TABLE IF NOT EXISTS bato_operator_heartbeat(at timestamptz NOT NULL); "
        "TRUNCATE bato_operator_heartbeat; INSERT INTO bato_operator_heartbeat VALUES(now());",
    )
    pg(
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-c",
        "DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_stat_archiver WHERE last_archived_time IS NULL "
        "OR last_archived_time < now()-interval '15 minutes' "
        "OR last_failed_time > last_archived_time) THEN "
        "RAISE EXCEPTION 'archive lag'; END IF; END $$;",
    )
    pg("pgbackrest", "--stanza=state", "check")
    info = json.loads(
        pg(
            "pgbackrest",
            "--stanza=state",
            "--output=json",
            "info",
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
    )
    age = datetime.datetime.now(datetime.UTC).timestamp() - max(
        b["timestamp"]["stop"] for b in info[0]["backup"]
    )
    if age > 26 * 3600:
        raise ValueError("State backup age exceeds 26 hours")
    usage = shutil.disk_usage(DATA)
    if usage.used / usage.total >= 0.8:
        raise ValueError("State disk exceeds 80 percent")
    context = ssl.create_default_context(cafile=str(CONFIG / "secrets/ca.crt"))
    with socket.create_connection(("127.0.0.1", 5432), timeout=10) as connection:
        connection.sendall(bytes.fromhex("0000000804d2162f"))
        if connection.recv(1) != b"S":
            raise ValueError("State TLS negotiation failed")
        with context.wrap_socket(connection, server_hostname=identity()["hostname"]) as tls:
            expires = ssl.cert_time_to_seconds(tls.getpeercert()["notAfter"])
            if expires - datetime.datetime.now(datetime.UTC).timestamp() < 21 * 86400:
                raise ValueError("State TLS expires within 21 days")
    node.run(
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--max-time",
        "20",
        "--config",
        str(CONFIG / "monitor.curl"),
        stdout=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "configure",
            "first-disk",
            "unlock",
            "initialize",
            "start",
            "stop",
            "gate",
            "database",
            "backup",
            "monitor",
            "firewall",
        ],
    )
    parser.add_argument("--source")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise ValueError("Authorized root operator required")
    if args.command not in ("gate", "start", "stop", "firewall"):
        lock = open("/run/lock/bato-state.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.command == "configure":
        configure(json.load(sys.stdin), args.source)
    elif args.command in ("first-disk", "unlock"):
        unlock(args.command == "first-disk")
    elif args.command == "stop":
        compose("stop")
    elif args.command == "gate":
        gate()
    elif args.command == "firewall":
        node.firewall(CONFIG / "firewall.nft")
    elif args.command == "monitor":
        monitor()
    elif args.command == "database":
        gate()
        database(json.load(sys.stdin))
    elif args.command == "backup":
        gate()
        kind = "full" if datetime.datetime.now(datetime.UTC).weekday() == 6 else "diff"
        pg("pgbackrest", "--stanza=state", f"--type={kind}", "backup")
    else:
        gate()
        if args.command == "initialize" and (DATA / "pgdata").exists():
            raise ValueError("Refusing to initialize existing state data")
        if args.command == "start" and (DATA / "pgdata/PG_VERSION").read_text().strip() != "16":
            raise ValueError("Existing PG16 data is required; initialization is explicit")
        compose("up", "-d", "--no-build", "--force-recreate", "--wait")
        if args.command == "initialize":
            pg("pgbackrest", "--stanza=state", "stanza-create")
            pg("pgbackrest", "--stanza=state", "--type=full", "backup")


if __name__ == "__main__":
    try:
        main()
    except (
        ValueError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        StopIteration,
        configparser.Error,
    ):
        sys.exit("State service operation refused; inspect private EU-local configuration.")
