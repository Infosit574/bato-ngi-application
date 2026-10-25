import logging
import os

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from bato.core.capabilities import DEFERRED_CAPABILITIES
from bato.mcp.registry import CONNECTORS, ENABLED_CONNECTORS


def _configure_logging() -> None:
    level = os.environ.get("BATO_LOG_LEVEL", "INFO")
    invalid = level not in {"DEBUG", "INFO", "WARNING", "ERROR"}
    if invalid:
        level = "INFO"
    logging.basicConfig(level=level)
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"):
        logging.getLogger(name).setLevel(level)
    if invalid:
        logging.getLogger(__name__).warning("Invalid BATO_LOG_LEVEL; falling back to INFO.")


_configure_logging()

app = FastAPI(
    title="BATO skeleton",
    version="0.1.0",
    description="Development skeleton by Infosit d.o.o. No AI or user-data services are enabled.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
async def ready() -> JSONResponse:
    database_url = os.environ.get("BATO_DATABASE_URL")
    if not database_url:
        return JSONResponse({"status": "not_ready", "database": "unconfigured"}, status_code=503)
    try:
        async with await psycopg.AsyncConnection.connect(
            database_url, connect_timeout=3, options="-c statement_timeout=3000"
        ) as connection:
            cursor = await connection.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            row = await cursor.fetchone()
    except psycopg.Error:
        return JSONResponse({"status": "not_ready", "database": "unavailable"}, status_code=503)
    if not row or not row[0]:
        return JSONResponse({"status": "not_ready", "database": "vector_missing"}, status_code=503)
    return JSONResponse({"status": "ready", "database": "ready", "vector": "enabled"})


@app.get("/status")
async def status() -> dict[str, object]:
    return {
        "stage": "skeleton",
        "implementer": "Infosit d.o.o.",
        "capabilities": dict.fromkeys(DEFERRED_CAPABILITIES, "not_implemented"),
        "connectors": [
            {
                "name": connector.name,
                "status": "stub" if connector in ENABLED_CONNECTORS else "disabled",
                "transport": "stdio",
                "tools": (
                    [tool.name for tool in connector.tools]
                    if connector in ENABLED_CONNECTORS
                    else []
                ),
            }
            for connector in CONNECTORS
        ],
    }
