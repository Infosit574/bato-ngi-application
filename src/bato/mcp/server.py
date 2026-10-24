import argparse
import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import ValidationError

from bato.mcp.contract import Connector
from bato.mcp.registry import CONNECTORS, ENABLED_CONNECTORS


def error_result(code: str, message: str) -> CallToolResult:
    return CallToolResult(
        isError=True,
        content=[TextContent(type="text", text=json.dumps({"code": code, "message": message}))],
    )


def create_server(connector: Connector) -> Server[Any, Any]:
    server: Server[Any, Any] = Server(f"bato-{connector.name}-stub", version="0.1.0")
    enabled = connector in ENABLED_CONNECTORS
    tools = {tool.name: tool for tool in connector.tools} if enabled else {}

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [tool.as_mcp_tool() for tool in tools.values()]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
        if not enabled:
            return error_result(
                "extension_disabled", f"The {connector.name} extension is disabled."
            )
        tool = tools.get(name)
        if tool is None:
            return error_result("unknown_tool", "This connector does not provide that tool.")
        try:
            tool.arguments.model_validate_json(json.dumps(arguments))
        except ValidationError:
            return error_result(
                "invalid_arguments", "Arguments do not match the tool input schema."
            )
        return error_result(
            "not_implemented",
            f"{name} is a stub. No external service was contacted and no data was changed."
            + (
                " Future writes require explicit user confirmation."
                if tool.requires_confirmation
                else ""
            ),
        )

    return server


async def serve(connector: Connector) -> None:
    server = create_server(connector)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BATO stdio MCP stubs; no external services are contacted."
    )
    parser.add_argument("connector", choices=[connector.name for connector in CONNECTORS])
    args = parser.parse_args()
    connector = next(connector for connector in CONNECTORS if connector.name == args.connector)
    if connector not in ENABLED_CONNECTORS:
        parser.error(f"The {connector.name} extension is disabled.")
    asyncio.run(serve(connector))


if __name__ == "__main__":
    main()
