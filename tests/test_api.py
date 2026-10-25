import itertools
import json
import os
import subprocess
import sys
from unittest.mock import AsyncMock, patch

import httpx
import psycopg
import pytest

from bato.api.app import app
from bato.mcp.registry import CONNECTORS

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def test_live_and_status_without_database(monkeypatch, client):
    monkeypatch.delenv("BATO_DATABASE_URL", raising=False)
    assert (await client.get("/health/live")).json() == {"status": "alive"}
    response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["database"] == "unconfigured"
    status = (await client.get("/status")).json()
    assert status["stage"] == "skeleton"
    assert set(status["capabilities"].values()) == {"not_implemented"}
    assert {connector["name"] for connector in status["connectors"]} == {
        "nextcloud",
        "rocketchat",
        "email",
    }
    assert all(connector["status"] == "stub" for connector in status["connectors"])
    assert (await client.get("/docs")).status_code == 404


async def test_readiness_database_failure_does_not_leak_credentials(monkeypatch, client):
    monkeypatch.setenv("BATO_DATABASE_URL", "postgresql://example:private-value@invalid/bato")
    with patch(
        "bato.api.app.psycopg.AsyncConnection.connect",
        new=AsyncMock(side_effect=psycopg.OperationalError("private-value")),
    ):
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
    assert "private-value" not in response.text
    assert (await client.get("/health/live")).status_code == 200


@pytest.mark.parametrize("vector_enabled,expected_status", [(True, 200), (False, 503)])
async def test_readiness_requires_vector(monkeypatch, client, vector_enabled, expected_status):
    monkeypatch.setenv("BATO_DATABASE_URL", "postgresql://invalid/bato")
    cursor = AsyncMock()
    cursor.fetchone.return_value = (vector_enabled,)
    connection = AsyncMock()
    connection.__aenter__.return_value = connection
    connection.execute.return_value = cursor
    with patch(
        "bato.api.app.psycopg.AsyncConnection.connect",
        new=AsyncMock(return_value=connection),
    ):
        response = await client.get("/health/ready")
    assert response.status_code == expected_status
    assert response.json()["database"] == ("ready" if vector_enabled else "vector_missing")


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "INFO"),
        ("DEBUG", "DEBUG"),
        ("INFO", "INFO"),
        ("WARNING", "WARNING"),
        ("ERROR", "ERROR"),
        ("TRACE", "INFO"),
        ("info", "INFO"),
        ("", "INFO"),
    ],
)
def test_log_level_uses_startup_configuration(value, expected):
    environment = os.environ.copy()
    environment.pop("BATO_LOG_LEVEL", None)
    if value is not None:
        environment["BATO_LOG_LEVEL"] = value
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib
import json
import logging
import os
import uvicorn

logging.basicConfig(level=logging.ERROR)
config = uvicorn.Config("bato.api.app:app")
config.load()
os.environ["BATO_LOG_LEVEL"] = "ERROR"
importlib.import_module("bato.api.app")
print(json.dumps([
    logging.getLevelName(logging.getLogger(name).getEffectiveLevel())
    for name in ("", "bato.api.app", "uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi")
]))
""",
        ],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert json.loads(probe.stdout) == [expected] * 6
    invalid = value not in {None, "DEBUG", "INFO", "WARNING", "ERROR"}
    warning = "WARNING:bato.api.app:Invalid BATO_LOG_LEVEL; falling back to INFO."
    assert probe.stderr.count(warning) == int(invalid)


@pytest.mark.parametrize("value", [None, "text", "json", "xml", "JSON", ""])
def test_log_format_uses_startup_configuration(value):
    environment = os.environ.copy()
    environment.pop("BATO_LOG_LEVEL", None)
    environment.pop("BATO_LOG_FORMAT", None)
    if value is not None:
        environment["BATO_LOG_FORMAT"] = value
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib
import logging
import os
import uvicorn

logging.basicConfig(level=logging.ERROR)
config = uvicorn.Config("bato.api.app:app")
config.load()
os.environ["BATO_LOG_FORMAT"] = "text" if os.environ.get("BATO_LOG_FORMAT") == "json" else "json"
importlib.import_module("bato.api.app")
for name in ("bato.api.app", "uvicorn", "uvicorn.error", "uvicorn.asgi"):
    logging.getLogger(name).info("startup probe")
logging.getLogger("uvicorn.access").info(
    '%s - "%s %s HTTP/%s" %d', "127.0.0.1:1234", "GET", "/health/live", "1.1", 200
)
""",
        ],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    lines = (probe.stderr + probe.stdout).splitlines()
    access_message = '127.0.0.1:1234 - "GET /health/live HTTP/1.1" 200'
    warning = "Invalid BATO_LOG_FORMAT; falling back to text."
    if value == "json":
        assert [json.loads(line) for line in lines] == [
            {"level": "INFO", "logger": name, "message": message}
            for name, message in [
                ("bato.api.app", "startup probe"),
                ("uvicorn", "startup probe"),
                ("uvicorn.error", "startup probe"),
                ("uvicorn.asgi", "startup probe"),
                ("uvicorn.access", access_message),
            ]
        ]
    else:
        invalid = value not in {None, "text"}
        assert lines == [
            *([f"WARNING:bato.api.app:{warning}"] if invalid else []),
            "INFO:bato.api.app:startup probe",
            *(["INFO:     startup probe"] * 3),
            f"INFO:     {access_message} OK",
        ]


@pytest.mark.parametrize("switches", [None, *itertools.product(("true", "false"), repeat=3)])
def test_extension_status_uses_startup_configuration(switches):
    environment = os.environ.copy()
    environment.pop("BATO_DATABASE_URL", None)
    for index, connector in enumerate(CONNECTORS):
        variable = f"BATO_MCP_{connector.name.upper()}_ENABLED"
        environment.pop(variable, None)
        if switches is not None:
            environment[variable] = switches[index]
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import asyncio
import json
import os
import httpx
from bato.api.app import app

async def inspect():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        status = (await client.get("/status")).json()
        for name in ("NEXTCLOUD", "ROCKETCHAT", "EMAIL"):
            variable = f"BATO_MCP_{name}_ENABLED"
            os.environ[variable] = "false" if os.environ.get(variable, "true") == "true" else "true"
        return {
            "status": status,
            "after": (await client.get("/status")).json(),
            "live": (await client.get("/health/live")).json(),
            "ready": (await client.get("/health/ready")).json(),
        }

print(json.dumps(asyncio.run(inspect())))
""",
        ],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    observed = json.loads(probe.stdout)
    assert observed["after"] == observed["status"]
    assert observed["live"] == {"status": "alive"}
    assert observed["ready"] == {"status": "not_ready", "database": "unconfigured"}
    for index, (connector, status) in enumerate(
        zip(CONNECTORS, observed["status"]["connectors"], strict=True)
    ):
        enabled = switches is None or switches[index] == "true"
        assert status == {
            "name": connector.name,
            "status": "stub" if enabled else "disabled",
            "transport": "stdio",
            "tools": [tool.name for tool in connector.tools] if enabled else [],
        }
