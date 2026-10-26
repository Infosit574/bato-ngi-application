"""Managed infrastructure checks. Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later."""

import importlib.util
import json
import os
import stat
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_node() -> ModuleType:
    spec = importlib.util.spec_from_file_location("managed_node", ROOT / "infra/scripts/node.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = load_node()
    monkeypatch.setattr(module, "CONFIG", tmp_path / "etc")
    monkeypatch.setattr(module, "DATA", tmp_path / "data")
    monkeypatch.setattr(module, "RELEASES", tmp_path / "releases")
    monkeypatch.setattr(module, "CURRENT", tmp_path / "current")
    monkeypatch.setattr(module.os, "fchown", lambda *args: None)
    return module


@pytest.fixture
def manifest() -> dict[str, object]:
    return {
        "tenant": "example",
        "location": "fsn1",
        "backup_location": "nbg1",
        "backup_bucket": "example-dev-backup-documentation",
        "environment": "dev",
        "volume_id": 123456,
        "volume_name": "example-dev-postgres",
        "device": "/dev/disk/by-id/scsi-0HC_Volume_123456",
        "source_commit": "1" * 40,
        "node_fqdn": "tenant.dev.bato.example.org",
        "acme_email": "operator@example.org",
        "admin_cidrs": ["192.0.2.0/28", "2001:db8:1::/64"],
        "tenant_cidrs": ["198.51.100.0/24", "2001:db8:2::/64"],
    }


@pytest.fixture
def bundle() -> dict[str, str]:
    return {
        "db_password": "synthetic-admin-canary",
        "api_password": r"synthetic:api\canary",
        "dns_token": "synthetic-dns-canary",
        "monitor_curl": 'url = "https://monitor.example.org/heartbeat/example-dev"\n',
        "pgbackrest_conf": (ROOT / "deploy/managed/pgbackrest.conf.example").read_text(),
    }


@pytest.mark.parametrize(
    "change",
    [
        {"source_commit": "main"},
        {"environment": "staging"},
        {"admin_cidrs": ["0.0.0.0/0", "::/0"]},
        {"tenant_cidrs": []},
        {"tenant_cidrs": ["192.0.2.0/24"]},
        {"volume_name": "example-prod-postgres"},
        {"device": "/dev/sda"},
        {"node_fqdn": "example.org`);bad"},
    ],
)
def test_manifest_rejects_unsafe_identity(
    node: ModuleType,
    manifest: dict[str, object],
    change: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        node.validate_manifest(manifest | change)


def test_render_keeps_both_families_restricted(
    node: ModuleType,
    manifest: dict[str, object],
) -> None:
    node.render(manifest)
    nft = (node.CONFIG / "firewall.nft").read_text()
    assert "ip saddr { 192.0.2.0/28 } tcp dport 22 accept" in nft
    assert "ip6 saddr { 2001:db8:2::/64 } tcp dport 443 accept" in nft
    assert "dport 80 " not in nft and "dport 5432 " not in nft
    proxy = json.loads((node.CONFIG / "proxy/traefik.json").read_text())
    assert proxy["api"]["dashboard"] is False
    assert set(proxy["providers"]) == {"file"}
    assert set(proxy["entryPoints"]) == {"https"}


def test_injection_is_atomic_private_and_escapes_libpq(
    node: ModuleType,
    manifest: dict[str, object],
    bundle: dict[str, str],
) -> None:
    node.render(manifest)
    node.inject(bundle)
    first = (node.CONFIG / "secrets/current").resolve()
    for name in node.SECRET_OWNERS:
        assert stat.S_IMODE((first / name).stat().st_mode) == 0o400
    assert (
        first / "api-pgpass"
    ).read_text() == r"db:5432:bato:bato_api:synthetic\:api\\canary" + "\n"
    with pytest.raises(ValueError):
        node.inject(
            bundle
            | {
                "pgbackrest_conf": bundle["pgbackrest_conf"].replace(
                    "expire-auto=n", "expire-auto=y"
                )
            }
        )
    assert (node.CONFIG / "secrets/current").resolve() == first
    node.inject(bundle | {"db_password": "rotated-synthetic-canary"})
    assert (node.CONFIG / "secrets/current").resolve() != first
    assert (first / "db-password").read_text() == "synthetic-admin-canary"
    assert "synthetic-" not in (node.CONFIG / "node.json").read_text()


def test_unmounted_volume_fails_before_source_or_initialization(
    node: ModuleType,
    manifest: dict[str, object],
) -> None:
    node.render(manifest)
    node.DATA.mkdir()
    with pytest.raises(ValueError, match="not mounted"):
        node.gate(initial=True)
    assert not (node.DATA / "pgdata").exists()


def test_backup_endpoint_must_match_retained_environment(
    node: ModuleType,
    manifest: dict[str, object],
    bundle: dict[str, str],
) -> None:
    node.render(manifest)
    bundle["pgbackrest_conf"] = bundle["pgbackrest_conf"].replace(
        "nbg1.your-objectstorage.com", "hel1.your-objectstorage.com"
    )
    with pytest.raises(ValueError, match="approved environment"):
        node.inject(bundle)
    assert not (node.CONFIG / "secrets/current").exists()


@pytest.mark.parametrize("permission", [None, 0o644])
def test_secret_gate_refuses_missing_or_readable_credentials(
    node: ModuleType,
    manifest: dict[str, object],
    bundle: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    permission: int | None,
) -> None:
    node.render(manifest)
    node.inject(bundle)
    monkeypatch.setattr(node, "disk_identity", lambda m: None)
    monkeypatch.setattr(
        node, "capture", lambda *args: manifest["source_commit"] if args[-1] == "HEAD" else ""
    )
    monkeypatch.setattr(node, "verify_images", lambda sha: None)
    monkeypatch.setattr(node, "SECRET_OWNERS", {name: os.getuid() for name in node.SECRET_OWNERS})
    credential = node.CONFIG / "secrets/current/api-pgpass"
    if permission is None:
        credential.unlink()
        with pytest.raises(FileNotFoundError):
            node.gate()
    else:
        credential.chmod(permission)
        with pytest.raises(ValueError, match="ownership or mode"):
            node.gate()


def test_wrong_mounted_device_rejected(
    node: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approved = tmp_path / "approved-disk"
    approved.touch()
    monkeypatch.setattr(Path, "is_mount", lambda p: p == node.DATA)
    monkeypatch.setattr(node, "capture", lambda *args: str(tmp_path / "other-disk"))
    with pytest.raises(ValueError, match="not the approved"):
        node.disk_identity({"device": str(approved)})


def test_missing_image_receipt_blocks_activation(
    node: ModuleType,
    manifest: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node.render(manifest)
    sha = str(manifest["source_commit"])
    (node.RELEASES / sha).mkdir(parents=True)
    monkeypatch.setattr(node, "capture", lambda *args: sha)
    with pytest.raises(FileNotFoundError):
        node.activate(sha, True)
    assert not node.CURRENT.exists()


def test_changed_image_is_not_an_approved_release(
    node: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "1" * 40
    node.atomic(node.CONFIG / "releases" / f"{sha}.json", json.dumps({"api": "sha256:old"}))
    monkeypatch.setattr(node, "capture", lambda *args: "sha256:changed")
    with pytest.raises(ValueError, match="Staged image changed"):
        node.verify_images(sha)


def test_managed_compose_has_no_development_secret_or_restart_bypass() -> None:
    output = subprocess.check_output(
        [
            "docker",
            "compose",
            "-f",
            "compose.yaml",
            "-f",
            "deploy/managed/compose.yaml",
            "config",
            "--format",
            "json",
        ],
        cwd=ROOT,
        env=dict(os.environ, BATO_SOURCE_COMMIT="1" * 40),
        text=True,
    )
    services = json.loads(output)["services"]
    assert "bato-development-only" not in output
    assert all(s["restart"] == "no" for s in services.values())
    assert services["db"]["environment"]["POSTGRES_PASSWORD_FILE"] == "/run/bato/db-password"
    assert "POSTGRES_PASSWORD" not in services["db"]["environment"]
    assert (
        services["api"]["environment"]["BATO_DATABASE_URL"] == "postgresql://bato_api@db:5432/bato"
    )
    assert services["api"]["ports"][0]["host_ip"] == "127.0.0.1"
    assert not services["db"].get("ports")
    assert all(
        v["bind"]["create_host_path"] is False
        for v in services["db"]["volumes"]
        if v["source"].startswith(("/srv/", "/etc/"))
    )
    assert "docker.sock" not in output
    assert services["proxy"]["network_mode"] == "host"
