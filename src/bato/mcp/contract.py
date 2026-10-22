from dataclasses import dataclass
from typing import Annotated

from mcp.types import Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

NonEmpty = Annotated[str, Field(min_length=1, max_length=4096)]


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    arguments: type[Arguments]
    read_only: bool = True
    requires_confirmation: bool = False

    def as_mcp_tool(self) -> Tool:
        return Tool(
            name=self.name,
            description=f"{self.description} Stub only; valid calls return not_implemented.",
            inputSchema=self.arguments.model_json_schema(),
            annotations=ToolAnnotations(
                readOnlyHint=self.read_only,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        )


@dataclass(frozen=True)
class Connector:
    name: str
    tools: tuple[ToolSpec, ...]
