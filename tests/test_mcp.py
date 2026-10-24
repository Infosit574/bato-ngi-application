import asyncio
import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from bato.mcp.registry import CONNECTORS

VALID_ARGUMENTS = {
    "nc_search": {
        "query": "budget",
        "date_range": {"start": "2026-01-01", "end": "2026-01-31"},
    },
    "nc_read": {"file_path": "/budget.txt"},
    "nc_list": {},
    "nc_metadata": {"file_path": "/budget.txt"},
    "nc_extract_knowledge": {
        "file_path": "/budget.txt",
        "topic_id": "12345678-1234-5678-1234-567812345678",
    },
    "rc_search": {"query": "budget"},
    "rc_channel_summary": {"channel_id": "example"},
    "rc_thread_context": {"thread_id": "example"},
    "email_search": {"query": "SUBJECT budget"},
    "email_read": {"message_id": "example"},
    "email_draft": {"to": ["person@example.invalid"], "subject": "budget", "body": "draft"},
}


def result_code(result):
    assert result.isError is True
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    return json.loads(result.content[0].text)["code"]


@pytest.mark.parametrize("connector", CONNECTORS, ids=lambda connector: connector.name)
@pytest.mark.parametrize("only_selected", [False, True], ids=["defaults", "only-selected"])
def test_stdio_discovery_and_fail_closed_calls(connector, only_selected):
    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "bato.mcp.server", connector.name],
            env=(
                {
                    f"BATO_MCP_{item.name.upper()}_ENABLED": (
                        "true" if item == connector else "false"
                    )
                    for item in CONNECTORS
                }
                if only_selected
                else {}
            ),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=10)
            ) as client:
                await client.initialize()
                discovered = (await client.list_tools()).tools
                assert {tool.name for tool in discovered} == {tool.name for tool in connector.tools}
                for tool in discovered:
                    assert tool.inputSchema["type"] == "object"
                    assert tool.inputSchema["additionalProperties"] is False
                    assert tool.annotations.readOnlyHint == (
                        tool.name not in {"email_draft", "nc_extract_knowledge"}
                    )
                    arguments = VALID_ARGUMENTS[tool.name]
                    if tool.inputSchema.get("required"):
                        assert (
                            result_code(await client.call_tool(tool.name, {}))
                            == "invalid_arguments"
                        )
                    assert result_code(await client.call_tool(tool.name, arguments)) == (
                        "not_implemented"
                    )
                    assert (
                        result_code(
                            await client.call_tool(tool.name, {**arguments, "unexpected": "value"})
                        )
                        == "invalid_arguments"
                    )
                    if tool.name in {"email_draft", "nc_extract_knowledge"}:
                        assert (
                            result_code(
                                await client.call_tool(tool.name, {**arguments, "confirmed": True})
                            )
                            == "not_implemented"
                        )
                assert result_code(await client.call_tool("missing_tool", {})) == "unknown_tool"
                first = discovered[0]
                assert (
                    result_code(
                        await client.call_tool(
                            first.name, {**VALID_ARGUMENTS[first.name], "query": 42}
                        )
                    )
                    == "invalid_arguments"
                )

    asyncio.run(exercise())


@pytest.mark.parametrize("connector", CONNECTORS, ids=lambda connector: connector.name)
def test_disabled_direct_server_discovery_and_dispatch(connector):
    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=[
                "-c",
                f"""
import asyncio
import os
from bato.mcp.registry import CONNECTORS
from bato.mcp.server import serve

os.environ["BATO_MCP_{connector.name.upper()}_ENABLED"] = "true"
asyncio.run(serve(next(item for item in CONNECTORS if item.name == "{connector.name}")))
""",
            ],
            env={f"BATO_MCP_{connector.name.upper()}_ENABLED": "false"},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=10)
            ) as client:
                await client.initialize()
                assert (await client.list_tools()).tools == []
                for tool in connector.tools:
                    assert (
                        result_code(await client.call_tool(tool.name, VALID_ARGUMENTS[tool.name]))
                        == "extension_disabled"
                    )
                assert result_code(await client.call_tool("missing_tool", {})) == (
                    "extension_disabled"
                )

    asyncio.run(exercise())


@pytest.mark.parametrize("connector", CONNECTORS, ids=lambda connector: connector.name)
def test_disabled_cli_fails_before_protocol_start(connector):
    environment = os.environ.copy()
    environment[f"BATO_MCP_{connector.name.upper()}_ENABLED"] = "false"
    result = subprocess.run(
        [str(Path(sys.executable).with_name("bato-mcp")), connector.name],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert f"The {connector.name} extension is disabled." in result.stderr


@pytest.mark.parametrize("connector", CONNECTORS, ids=lambda connector: connector.name)
@pytest.mark.parametrize("value", ["", "TRUE", "1", " false "])
@pytest.mark.parametrize(
    "arguments",
    [("-m", "bato.mcp.server", "nextcloud"), ("-c", "import bato.api.app")],
    ids=["mcp", "api"],
)
def test_invalid_extension_configuration_fails_startup(connector, value, arguments):
    environment = os.environ.copy()
    variable = f"BATO_MCP_{connector.name.upper()}_ENABLED"
    environment[variable] = value
    result = subprocess.run(
        [sys.executable, *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert f"{variable} must be 'true' or 'false' (lowercase)." in result.stderr


def test_nextcloud_date_range_and_confirmation_schema():
    tools = {tool.name: tool for connector in CONNECTORS for tool in connector.tools}
    assert set(tools) == set(VALID_ARGUMENTS)
    with pytest.raises(ValueError, match="end must not precede start"):
        tools["nc_search"].arguments.model_validate_json(
            json.dumps(
                {
                    "query": "budget",
                    "date_range": {"start": "2026-02-01", "end": "2026-01-01"},
                }
            )
        )
    for name in ("email_draft", "nc_extract_knowledge"):
        schema = tools[name].as_mcp_tool().inputSchema
        assert schema["properties"]["confirmed"]["default"] is False
