import asyncio
import itertools
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

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


@pytest.mark.parametrize(
    "switches", [None, *itertools.product(("true", "false"), repeat=3), ("", "", "")]
)
def test_compose_extension_environment(monkeypatch, switches):
    variables = [f"BATO_MCP_{name}_ENABLED" for name in ("NEXTCLOUD", "ROCKETCHAT", "EMAIL")]
    for index, variable in enumerate(variables):
        monkeypatch.delenv(variable, raising=False)
        if switches is not None:
            monkeypatch.setenv(variable, switches[index])
    configuration = json.loads(compose("--env-file", "/dev/null", "config", "--format", "json"))
    environment = configuration["services"]["api"]["environment"]
    assert [environment[variable] for variable in variables] == (
        list(switches) if switches is not None else ["true"] * 3
    )


def test_compose_extension_switches_and_recreation(monkeypatch, tmp_path):
    for name in ("NEXTCLOUD", "ROCKETCHAT", "EMAIL"):
        monkeypatch.delenv(f"BATO_MCP_{name}_ENABLED", raising=False)
    env_file = tmp_path / "extensions.env"
    env_file.write_text(
        "BATO_MCP_NEXTCLOUD_ENABLED=false\n"
        "BATO_MCP_ROCKETCHAT_ENABLED=true\n"
        "BATO_MCP_EMAIL_ENABLED=false\n"
    )
    prefix = ("--env-file", str(env_file))
    compose(*prefix, "up", "-d", "--force-recreate", "--wait", "api")
    await_ready()
    status = get("/status")[1]["connectors"]
    assert [connector["status"] for connector in status] == ["disabled", "stub", "disabled"]
    assert status[0]["tools"] == status[2]["tools"] == []
    for name in ("nextcloud", "email"):
        result = subprocess.run(
            [
                "docker",
                "compose",
                *prefix,
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "api",
                "bato-mcp",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 2
        assert result.stdout == ""
        assert f"The {name} extension is disabled." in result.stderr

    async def exercise_stdio():
        params = StdioServerParameters(
            command="docker",
            args=[
                "compose",
                *prefix,
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "api",
                "bato-mcp",
                "rocketchat",
            ],
            cwd=str(ROOT),
            env={
                variable: os.environ[variable]
                for variable in ("COMPOSE_PROJECT_NAME", "BATO_API_PORT")
                if variable in os.environ
            },
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=30)
            ) as client:
                await client.initialize()
                assert {tool.name for tool in (await client.list_tools()).tools} == set(
                    status[1]["tools"]
                )
                result = await client.call_tool("rc_search", {"query": "budget"})
                assert result.isError is True
                assert isinstance(result.content[0], TextContent)
                assert json.loads(result.content[0].text)["code"] == "not_implemented"

    asyncio.run(exercise_stdio())
    env_file.write_text(
        "BATO_MCP_NEXTCLOUD_ENABLED=true\n"
        "BATO_MCP_ROCKETCHAT_ENABLED=true\n"
        "BATO_MCP_EMAIL_ENABLED=true\n"
    )
    compose(*prefix, "restart", "api")
    await_ready()
    assert get("/status")[1]["connectors"] == status
    compose(*prefix, "up", "-d", "--force-recreate", "--wait", "api")
    await_ready()
    assert all(connector["status"] == "stub" for connector in get("/status")[1]["connectors"])
