import os

from bato.mcp.contract import Connector
from bato.mcp.email import CONNECTOR as EMAIL
from bato.mcp.nextcloud import CONNECTOR as NEXTCLOUD
from bato.mcp.rocketchat import CONNECTOR as ROCKETCHAT

CONNECTORS = (NEXTCLOUD, ROCKETCHAT, EMAIL)


def _is_enabled(connector: Connector) -> bool:
    variable = f"BATO_MCP_{connector.name.upper()}_ENABLED"
    value = os.environ.get(variable, "true")
    if value not in {"true", "false"}:
        raise ValueError(f"{variable} must be 'true' or 'false' (lowercase).")
    return value == "true"


ENABLED_CONNECTORS = tuple(connector for connector in CONNECTORS if _is_enabled(connector))
