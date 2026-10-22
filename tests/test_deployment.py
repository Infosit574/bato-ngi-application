import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import pytest

pytestmark = pytest.mark.deployment
ROOT = Path(__file__).resolve().parents[1]
BASE_URL = f"http://127.0.0.1:{os.environ.get('BATO_API_PORT', '8000')}"


def compose(*args):
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    ).stdout.strip()


def get(path):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=6) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def await_ready():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            if get("/health/ready")[0] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    pytest.fail("API did not regain database readiness within 90 seconds")


def sql(query):
    return compose("exec", "-T", "db", "psql", "-U", "bato", "-d", "bato", "-Atc", query)


def test_compose_readiness_persistence_and_recovery():
    await_ready()
    assert get("/health/ready")[1] == {
        "status": "ready",
        "database": "ready",
        "vector": "enabled",
    }
    assert sql("SELECT extversion FROM pg_extension WHERE extname = 'vector'") == "0.8.2"
    assert sql("SELECT '[1,2,3]'::vector <-> '[1,2,3]'::vector") == "0"
    assert get("/status")[1]["stage"] == "skeleton"
    assert compose("port", "api", "8000") == f"127.0.0.1:{BASE_URL.rsplit(':', 1)[1]}"
    configuration = json.loads(compose("config", "--format", "json"))
    assert not configuration["services"]["db"].get("ports")
    marker = str(uuid4())
    sql("CREATE TABLE IF NOT EXISTS deployment_probe (id uuid PRIMARY KEY)")
    sql(f"INSERT INTO deployment_probe (id) VALUES ('{marker}')")
    compose("stop", "db")
    try:
        assert get("/health/ready")[0] == 503
        assert get("/health/live") == (200, {"status": "alive"})
    finally:
        compose("start", "db")
    await_ready()
    compose("restart")
    await_ready()
    assert sql(f"SELECT id FROM deployment_probe WHERE id = '{marker}'") == marker
    compose("down")
    compose("up", "-d", "--wait", "--wait-timeout", "120")
    await_ready()
    assert sql(f"SELECT id FROM deployment_probe WHERE id = '{marker}'") == marker
    sql("DROP EXTENSION vector")
    try:
        assert get("/health/ready") == (
            503,
            {"status": "not_ready", "database": "vector_missing"},
        )
    finally:
        sql("CREATE EXTENSION vector")
    await_ready()
    sql(f"DELETE FROM deployment_probe WHERE id = '{marker}'")
