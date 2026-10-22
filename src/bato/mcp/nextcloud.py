from datetime import date
from uuid import UUID

from pydantic import Field, model_validator

from bato.mcp.contract import Arguments, Connector, NonEmpty, ToolSpec


class DateRange(Arguments):
    start: date
    end: date

    @model_validator(mode="after")
    def ordered(self) -> "DateRange":
        if self.end < self.start:
            raise ValueError("end must not precede start")
        return self


class Search(Arguments):
    query: NonEmpty
    folder_path: NonEmpty = "/"
    file_types: list[NonEmpty] = Field(default_factory=list, max_length=100)
    date_range: DateRange | None = None


class Read(Arguments):
    file_path: NonEmpty
    extract_text: bool = True
    summarize: bool = False


class ListFiles(Arguments):
    folder_path: NonEmpty = "/"
    recursive: bool = False
    filter: NonEmpty | None = None


class Metadata(Arguments):
    file_path: NonEmpty
    include_versions: bool = False


class ExtractKnowledge(Arguments):
    file_path: NonEmpty
    topic_id: UUID
    confirmed: bool = False


CONNECTOR = Connector(
    "nextcloud",
    (
        ToolSpec("nc_search", "Search documents.", Search),
        ToolSpec("nc_read", "Read a document.", Read),
        ToolSpec("nc_list", "List a folder.", ListFiles),
        ToolSpec("nc_metadata", "Read document metadata.", Metadata),
        ToolSpec(
            "nc_extract_knowledge",
            "Extract facts into memory; future writes require user confirmation.",
            ExtractKnowledge,
            read_only=False,
            requires_confirmation=True,
        ),
    ),
)
