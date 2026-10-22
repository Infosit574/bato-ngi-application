
# BATO – Open-Source Cognitive AI Butler for Digital Sovereignty
Implemented by **Infosit d.o.o.**, Poreč, Croatia.

## Current status: initial skeleton

This repository now runs a development API and PostgreSQL with pgvector. It also
provides discoverable stdio MCP **stubs** for Nextcloud, Rocket.Chat, and Email.
It does **not** provide chat, AI inference, offline AI assistance, authentication,
memory algorithms, tenant isolation, or working external integrations.

The NGI co-funding application was unsuccessful. The documents in `docs/` remain
historical design context, not programme obligations. See
[scope and design decisions](docs/skeleton-scope.md) for implemented sections,
departures, deferred features, and decisions for human confirmation.

## Start with Docker Compose

Install Docker Engine or Docker Desktop with Compose v2.20+ and run from this checkout:

```sh
docker compose up --build --wait
```

No `.env` copy, provider token, GPU, model download, or cloud account is required.
The first build needs network access for open-source images and Python packages.
The running skeleton makes no cloud or connector calls.

- Liveness: <http://127.0.0.1:8000/health/live>
- Database and vector readiness: <http://127.0.0.1:8000/health/ready>
- Truthful capability and connector inventory: <http://127.0.0.1:8000/status>

There is no web chat UI. The HTTP API binds to loopback on the host; PostgreSQL
has no published host port. **The database credentials are public development
defaults. This is not a production deployment.**

See [deployment and development](docs/development.md) for persistence, diagnostics,
checks, optional settings, and [MCP stubs](docs/mcp-stubs.md) for client commands.

## Overview
BATO is an open-source cognitive AI architecture designed to empower small communities (up to 150 members) and SMEs to achieve digital sovereignty. The longer-term intent is offline-first operation, European multilingual models, and privacy-aware orchestration of external services. These are design goals, not capabilities delivered by this skeleton.

**Planned capabilities**
- Memory triage algorithm for persistent insights
- Semantic topic extraction across multi-session dialogues
- Cognitive orchestration for local/cloud AI coordination
- MCP extensions (Nextcloud, Rocket.Chat, Email)
- One-click deployment (Docker Compose, OVA image)
- ActivityPub-ready schema for future federation

**Target Users**
- SMEs (up to 150 employees)
- Rural communities and minority organizations
- Public sector entities seeking CLOUD Act resilience

## License

Software is **AGPL v3 or later**, as granted in the unchanged [license.txt](license.txt).
Documentation is **CC BY-SA 4.0**. Copyright (C) 2026 Infosit d.o.o.
Full texts are in `LICENSES/`; [licensing and dependencies](docs/licensing.md)
describes the scope and third-party notices. No model weights are included.

**Links**
- Website: [https://bato.infosit.hr](https://bato.infosit.hr) *(planned)*
- GitHub: [https://github.com/Infosit574/bato-ngi-application](https://github.com/Infosit574/bato-ngi-application)

**Contact**
Infosit d.o.o.  
Email: info@infosit.com
Location: Poreč, Croatia
