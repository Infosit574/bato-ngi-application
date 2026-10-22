# MCP connector stubs

Implemented by Infosit d.o.o. Documentation: CC BY-SA 4.0.

Each connector is a real stdio MCP server using the official Python SDK. It
supports initialization, `tools/list`, and `tools/call`. There is no HTTP MCP
transport and the REST `/status` endpoint is not an MCP server.

After `uv sync --locked`, configure an MCP client to launch one of these commands
from the repository root:

```sh
uv run --locked bato-mcp nextcloud
uv run --locked bato-mcp rocketchat
uv run --locked bato-mcp email
```

For a client that needs an executable path, use this checkout's
`.venv/bin/bato-mcp` and a single argument (`nextcloud`, `rocketchat`, or `email`).
These are long-lived stdio processes, not interactive shells. Keep stdout for
the protocol. No database or API process is required.
After building the image, a client can instead launch a container over stdio:

```sh
docker compose run --rm --no-deps -T api bato-mcp nextcloud
```

All valid tool calls return an MCP tool result with `isError: true` and a JSON
text payload whose code is `not_implemented`. Bad arguments return
`invalid_arguments`; unknown tool names return `unknown_tool`.
No call returns invented documents, messages, summaries, drafts, or an empty
success result. No call contacts an external service, reads credentials, sends
messages, writes extracted knowledge, or persists drafts, even when `confirmed`
is true. There is no credential configuration in the stubs.

## Tool contract

The server publishes JSON input schemas. Extra arguments are rejected. Strings
are non-empty and at most 4096 characters; bounded lists permit at most 100 items.
These provisional limits and the following defaults are reversible choices, not
requirements from the historical application:

| Connector/tool | Required inputs | Optional inputs and defaults |
| --- | --- | --- |
| Nextcloud `nc_search` | `query` | `folder_path="/"`, `file_types=[]` (no restriction), `date_range=null` |
| Nextcloud `nc_read` | `file_path` | `extract_text=true`, `summarize=false` |
| Nextcloud `nc_list` | none | `folder_path="/"`, `recursive=false`, `filter=null` |
| Nextcloud `nc_metadata` | `file_path` | `include_versions=false` |
| Nextcloud `nc_extract_knowledge` | `file_path`, `topic_id` (UUID) | `confirmed=false` |
| Rocket.Chat `rc_search` | `query` | `channel_id=null` (unspecified channel) |
| Rocket.Chat `rc_channel_summary` | `channel_id` | none |
| Rocket.Chat `rc_thread_context` | `thread_id` | none |
| Email `email_search` | `query` | `mailbox="INBOX"` |
| Email `email_read` | `message_id` | `mailbox="INBOX"` |
| Email `email_draft` | `to` (non-empty string list), `subject`, `body` | `confirmed=false` |

`date_range`, when supplied, contains ISO date strings `start` and `end` with
`end >= start`. Folder/file paths, search/filter syntax, email message identifiers,
address validation, pagination, and date-boundary/timezone semantics must be
confirmed against the real providers before integration. The stubs do not resolve
paths or interpret queries. Draft addresses are not claimed to be validated email
addresses.

## Safety boundary for later work

Read tools advertise read-only hints. Knowledge extraction and email drafting do
not: they represent future writes and require explicit human confirmation before
any write can be added. The current `confirmed` schema field is not authorization
or proof of a human decision; a real implementation needs a trusted confirmation
flow. Idempotence currently describes a stub with no side effects, not the future
write implementation. No send tool is exposed.

Per-user credential isolation, authorization, and privacy-safe audit events remain
deferred. Do not log tokens or raw personal tool arguments to implement auditing.
No connector is advertised as ready or connected merely because discovery works.
