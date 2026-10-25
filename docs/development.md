# Deployment and development

Implemented by Infosit d.o.o. Documentation: CC BY-SA 4.0.

## Local baseline

Docker Engine/Desktop with Compose v2.20+ is the only prerequisite for the
container deployment. Start from the repository root:

```sh
docker compose up --build --wait
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:8000/status
```

The locally built API runs as UID 10001. The PostgreSQL 16 image includes pgvector
0.8.2. Initialization enables the vector extension in the `bato` database.
Startup waits for PostgreSQL health, then API health. API readiness executes a
database query and requires the vector extension; database loss returns HTTP 503.
Liveness remains HTTP 200 while the API process can serve requests.
Readiness does not mean AI or connectors are implemented.

No model download or accelerator is involved. Only the initial build/pull needs
internet access. A later build can still require the network; this is not an
offline installation package. No cloud provider is called by the application.

The API is published at `127.0.0.1:8000`; the database is reachable only on the
Compose network. Set `BATO_API_PORT=8080` in the shell or an optional `.env`
to use another host port. `.env.example` lists this setting; it is not required.
The three `BATO_MCP_*_ENABLED` switches in `.env.example` default to `true`.
Set unused extensions to `false` in `.env` or the shell before deployment.
See [MCP startup switches](mcp-stubs.md#startup-extension-switches) for accepted
values, standalone client configuration, and container recreation requirements.
`BATO_LOG_LEVEL` sets the API process log level at startup, including Uvicorn
error and access logs. Accepted values are `DEBUG`, `INFO`, `WARNING`, and `ERROR`
(uppercase). The default is `INFO`; invalid values fall back to `INFO` with a warning.
`BATO_LOG_FORMAT` selects `text` or `json` (lowercase) for application and Uvicorn
log lines at startup. The default is `text`; invalid values fall back to `text`
with a warning. JSON lines contain `level`, `logger`, and `message`; exception
tracebacks are included in the message with escaped newlines.
Set these in `.env` or the shell before deployment, then recreate the API container
with `docker compose up -d --force-recreate api`. For local Python execution, set
them in the process environment before starting the API; later changes have no effect.
For local Python execution, `BATO_DATABASE_URL` is a libpq-compatible connection
string supplied by the operator; no application-side default is assumed.

## Data lifecycle and diagnostics

PostgreSQL data lives in the Compose project's `postgres-data` named volume.
Both restart and container recreation preserve it:

```sh
docker compose restart
docker compose down
docker compose up --wait
docker compose ps
docker compose logs api db
```

`docker compose down` stops services without deleting the named volume.
Do not add `--volumes` unless you intend to erase the database.
Changing the Compose project name selects a different volume.
Initialization SQL runs only for a new empty volume; it is not a migration system.
If an existing development database lacks the vector extension, enable it explicitly:

```sh
docker compose exec db psql -U bato -d bato -c 'CREATE EXTENSION IF NOT EXISTS vector'
```

There are no business tables yet. The historical SQL is conceptual and must not be
run as a migration. Future schema work needs authorization, migration, and backup
design rather than automatic table creation on application startup.

## Security limits

The public `bato-development-only` password and `bato` database superuser exist
solely for this local skeleton. There is no authentication, TLS, secret store,
tenant isolation, audit system, backup/restore policy, or production hardening.
Do not load sensitive data or expose this deployment to a LAN or the internet.
Loopback binding is not protection from other users/processes on the same host.
Do not put real provider tokens in Compose or the shared database.

Production support requires a separate reviewed deployment design: per-service
least-privilege roles, managed secrets, authenticated access, TLS, network policy,
backup/restore testing, resource limits, monitoring, and update procedures.
Changing one password does not make this baseline production-ready.

## Python development and checks

Use Python 3.12 or 3.13 and uv 0.11.4. The lockfile pins runtime and development
dependencies, including transitive dependencies and platform markers.

```sh
uv sync --locked --python 3.12
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

`uv run pytest` runs API behavior and real subprocess/stdio MCP protocol tests.
To prove actual deployment behavior, use a disposable development Compose project
with no valuable data:

```sh
docker compose up --build --wait
uv run pytest -m deployment
```

The deployment test stops the database, restarts services, recreates containers,
and temporarily removes the vector extension. It verifies readiness failure and
recovery, an actual vector operation, loopback publication, and a marker surviving
restart and named-volume reuse. It creates a `deployment_probe` table in that
development database. Do not run it against real data.
It also checks all extension-switch combinations in Compose configuration,
`.env` propagation to the API and one-off MCP containers, disabled CLI rejection,
and the difference between restarting and recreating a configured container.

CI runs the same code checks and deployment lifecycle on Linux. macOS, Windows,
ARM hardware, OVA images, and production operation have not been validated.
