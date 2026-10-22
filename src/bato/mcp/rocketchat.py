from bato.mcp.contract import Arguments, Connector, NonEmpty, ToolSpec


class Search(Arguments):
    query: NonEmpty
    channel_id: NonEmpty | None = None


class ChannelSummary(Arguments):
    channel_id: NonEmpty


class ThreadContext(Arguments):
    thread_id: NonEmpty


CONNECTOR = Connector(
    "rocketchat",
    (
        ToolSpec("rc_search", "Search messages without posting.", Search),
        ToolSpec("rc_channel_summary", "Summarize a channel without posting.", ChannelSummary),
        ToolSpec("rc_thread_context", "Read thread context.", ThreadContext),
    ),
)
