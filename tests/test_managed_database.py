"""Physical recovery proof. Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later."""

import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.deployment
ROOT = Path(__file__).resolve().parents[1]


def docker(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.check_output(["docker", *args], input=data)


def test_file_credentials_encrypted_physical_pitr(tmp_path: Path) -> None:
    name = f"bato-pitr-{uuid.uuid4().hex[:12]}"
    image = "bato-pgbackrest-acceptance"
    docker("build", "-q", "-t", image, "-f", "deploy/managed/postgres.Dockerfile", str(ROOT))
    docker("create", "--name", name, image, "sleep", "infinity")
    docker("start", name)
    canaries = {"admin": secrets.token_urlsafe(32), "api-password": secrets.token_urlsafe(32)}
    cipher = secrets.token_urlsafe(48)
    config = (
        "[global]\nrepo1-type=posix\nrepo1-path=/repository\n"
        f"repo1-cipher-type=aes-256-cbc\nrepo1-cipher-pass={cipher}\n"
        "expire-auto=n\narchive-async=n\nstart-fast=y\nlog-level-console=warn\nlog-level-file=off\n"
        "[bato]\npg1-path=/var/lib/postgresql/data/pgdata\n"
        "pg1-socket-path=/var/run/postgresql\n"
    )
    try:
        docker(
            "exec",
            name,
            "mkdir",
            "-p",
            "/run/bato",
            "/repository",
            "/restore",
            "/var/run/postgresql",
            "/var/lib/postgresql/data",
        )
        for filename, value in canaries.items():
            path = tmp_path / filename
            path.write_text(value)
            docker("cp", str(path), f"{name}:/run/bato/{filename}")
        path = tmp_path / "pgbackrest.conf"
        path.write_text(config)
        docker("cp", str(path), f"{name}:/etc/pgbackrest/pgbackrest.conf")
        docker("cp", str(ROOT / "deploy/managed/initdb.sql"), f"{name}:/tmp/initdb.sql")
        docker(
            "exec",
            name,
            "chown",
            "-R",
            "999:999",
            "/run/bato",
            "/repository",
            "/restore",
            "/var/run/postgresql",
            "/var/lib/postgresql/data",
            "/etc/pgbackrest",
        )
        docker(
            "exec",
            name,
            "chmod",
            "0400",
            "/run/bato/admin",
            "/run/bato/api-password",
            "/etc/pgbackrest/pgbackrest.conf",
        )

        def pg(*args: str, data: bytes | None = None) -> bytes:
            return docker("exec", "-i", "-u", "postgres", name, *args, data=data)

        def sql(statement: str, port: str = "5432") -> str:
            return (
                pg(
                    "psql",
                    "-X",
                    "-At",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-U",
                    "postgres",
                    "-d",
                    "postgres",
                    "-p",
                    port,
                    "-c",
                    statement,
                )
                .decode()
                .strip()
            )

        pg(
            "initdb",
            "-D",
            "/var/lib/postgresql/data/pgdata",
            "--username=postgres",
            "--pwfile=/run/bato/admin",
            "--auth-local=trust",
            "--auth-host=scram-sha-256",
        )
        pg(
            "pg_ctl",
            "-D",
            "/var/lib/postgresql/data/pgdata",
            "-l",
            "/tmp/postgres.log",
            "-o",
            "-c archive_mode=on -c wal_level=replica -c archive_timeout=300s "
            "-c 'archive_command=pgbackrest --stanza=bato archive-push %p'",
            "start",
        )
        sql("CREATE DATABASE bato")
        pg(
            "psql",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "postgres",
            "-d",
            "bato",
            "-f",
            "/tmp/initdb.sql",
        )
        assert sql("SELECT rolsuper FROM pg_roles WHERE rolname='bato_api'") == "f"
        passfile = tmp_path / "api-pgpass"
        passfile.write_text(f"127.0.0.1:5432:bato:bato_api:{canaries['api-password']}\n")
        docker("cp", str(passfile), f"{name}:/run/bato/api-pgpass")
        docker("exec", name, "chown", "10001:10001", "/run/bato/api-pgpass")
        docker("exec", name, "chmod", "0400", "/run/bato/api-pgpass")
        assert (
            docker(
                "exec",
                "-u",
                "10001:10001",
                "-e",
                "PGPASSFILE=/run/bato/api-pgpass",
                name,
                "psql",
                "-X",
                "-At",
                "-h",
                "127.0.0.1",
                "-U",
                "bato_api",
                "-d",
                "bato",
                "-c",
                "SELECT '[1,2,3]'::vector <-> '[1,2,3]'::vector",
            ).strip()
            == b"0"
        )
        sql("CREATE TABLE restore_marker(value text); INSERT INTO restore_marker VALUES ('base')")
        pg("pgbackrest", "--stanza=bato", "stanza-create")
        pg("pgbackrest", "--stanza=bato", "--type=full", "backup")
        time.sleep(1.1)
        sql("INSERT INTO restore_marker VALUES ('retained')")
        target = sql("SELECT clock_timestamp()")
        time.sleep(0.2)
        sql("INSERT INTO restore_marker VALUES ('excluded')")
        sql("SELECT pg_switch_wal()")
        pg("pgbackrest", "--stanza=bato", "check")
        pg("pg_ctl", "-D", "/var/lib/postgresql/data/pgdata", "-m", "fast", "stop")
        pg(
            "pgbackrest",
            "--stanza=bato",
            "--pg1-path=/restore/pgdata",
            "--type=time",
            f"--target={target}",
            "--target-action=promote",
            "restore",
        )
        pg(
            "pg_ctl",
            "-D",
            "/restore/pgdata",
            "-l",
            "/tmp/restore.log",
            "-o",
            "-p 5433 -c archive_mode=off",
            "start",
        )
        assert (
            sql("SELECT string_agg(value, ',' ORDER BY value) FROM restore_marker", "5433")
            == "base,retained"
        )
        assert sql("SELECT pg_is_in_recovery()", "5433") == "f"
        assert (
            pg(
                "psql",
                "-X",
                "-At",
                "-U",
                "postgres",
                "-d",
                "bato",
                "-p",
                "5433",
                "-c",
                "SELECT '[1,2,3]'::vector <-> '[1,2,3]'::vector",
            ).strip()
            == b"0"
        )
        docker("cp", f"{name}:/repository/backup/bato/backup.info", str(tmp_path / "ciphertext"))
        assert (tmp_path / "ciphertext").read_bytes().startswith(b"Salted__")
        info = json.loads(docker("inspect", name))
        public_surfaces = (
            json.dumps(info).encode()
            + docker("logs", name)
            + pg("cat", "/tmp/postgres.log", "/tmp/restore.log")
            + docker("top", name, "-eo", "pid,args")
        )
        assert all(value.encode() not in public_surfaces for value in [*canaries.values(), cipher])
    finally:
        docker("rm", "-f", "-v", name)
