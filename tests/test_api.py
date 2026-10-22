from unittest.mock import AsyncMock, patch

import httpx
import psycopg
import pytest

from bato.api.app import app

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
