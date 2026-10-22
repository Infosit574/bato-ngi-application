from pydantic import Field

from bato.mcp.contract import Arguments, Connector, NonEmpty, ToolSpec


class Search(Arguments):
    query: NonEmpty
    mailbox: NonEmpty = "INBOX"


class Read(Arguments):
    message_id: NonEmpty
    mailbox: NonEmpty = "INBOX"


class Draft(Arguments):
    to: list[NonEmpty] = Field(min_length=1, max_length=100)
    subject: NonEmpty
    body: NonEmpty
    confirmed: bool = False


CONNECTOR = Connector(
    "email",
    (
        ToolSpec("email_search", "Search email without changing messages.", Search),
        ToolSpec("email_read", "Read an email without changing it.", Read),
        ToolSpec(
            "email_draft",
            "Compose a draft; future draft creation requires user confirmation. Never send.",
            Draft,
            read_only=False,
            requires_confirmation=True,
        ),
    ),
)
