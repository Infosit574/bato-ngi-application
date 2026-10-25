# ADR-0001: Configurable API log format

Implemented by Infosit d.o.o. Documentation: CC BY-SA 4.0.

## Context

The API reads `BATO_LOG_LEVEL` at startup. Operators also need to select plain-text
or JSON log lines without adding dependencies.

## Decision

Read `BATO_LOG_FORMAT` at the same startup point. Accept lowercase `text` and
`json`, default to `text`, and warn when an invalid value falls back to `text`.
Apply the format to application and Uvicorn logs without changing log levels.
Expose the `text` default in Compose and `.env.example`.

## Consequences

Existing deployments retain their text output. JSON logs use the standard library
and contain `level`, `logger`, and `message`, with tracebacks escaped in the message.
Changing the setting requires a process restart or API container recreation.
