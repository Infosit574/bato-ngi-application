# Initial skeleton: scope and design decisions

Implemented by Infosit d.o.o. Documentation: CC BY-SA 4.0.

The NGI co-funding application was unsuccessful. The original documents remain
unchanged as historical context. Budgets, schedules, pilots, programme alignment,
and programme-specific norms impose no current design constraints. Open-source
licensing and Infosit d.o.o.'s implementer attribution remain in force.

## Implemented from the specification's intent

- **§§4.1–4.3, architecture and stack:** installable Python/FastAPI package,
  operational API, PostgreSQL 16 with pgvector, and separate API, core, domain,
  and MCP boundaries. Core protocols describe authentication, memory, routing,
  and orchestration obligations; none supplies a fake implementation.
- **§4.2, domain vocabulary:** UUID identities, community/user/group references,
  hierarchical topics, memory kinds, private/group/community visibility, and
  private-by-default provider requests as in-memory types. These are not database
  tables, validated security policies, RLS, or federation support.
- **§§5.2–5.6, connector surface:** Nextcloud's five, Rocket.Chat's three, and
  Email's three named tools are discoverable in real stdio MCP servers with input
  schemas, read-only hints, and deterministic error results. No actual integration,
  credential storage, audit system, extraction write, or draft persistence exists.
- **§§6.1–6.2 and WP1, deployment foundation:** one-command source build/start,
  database/vector readiness, health-conditioned startup, persistent database
  storage, tests, and CI. The container image runs the API as a non-root user.
- **§12 and sustainability intent:** retain the existing AGPL-3.0-or-later software
  grant, CC BY-SA 4.0 documentation, Infosit attribution, and modular provider
  boundaries. Pinned dependencies and images have a documented license review.

## Deliberate departures and deferred work

1. **Narrow skeleton, not the old full MVP (§6.1):** model inference/downloads,
   EuroLLM, llama.cpp/vLLM, Mem0, RouteLLM, memory triage/topic algorithms,
   embeddings/morphological NLP, real providers, and offline knowledge are absent.
   This keeps startup CPU-only and hardware-independent without implying
   delivered offline AI functionality or selecting an unvalidated AI stack.
2. **No executable business schema yet (§4.2):** the original SQL is conceptual
   pseudocode. Only vector-extension initialization is shipped. The domain types
   preserve vocabulary without promising an unreviewed tenancy, retention,
   embedding dimension, or ActivityPub schema. Migrations and full RLS/auth must
   be designed together before storing user data.
3. **All connectors are stubs (§§5.3–5.5):** even Nextcloud's proposed full
   integration is deferred. Real MCP discovery is useful now, but mocked successes
   would misrepresent readiness. Write-like tool schemas reserve confirmation;
   no sending capability or shared credentials are introduced.
4. **Build from source instead of pre-built application images (§6.2):** there is
   no published BATO image to trust or depend on. Images for the build tool,
   Python, and pgvector are pinned by digest; Python dependencies are locked.
5. **Loopback address instead of `bato.local` (§6.2):** the skeleton provides no
   mDNS/DNS provisioning, TLS, login, or first-run wizard. Explicit loopback
   publication avoids an unconfigured hostname and accidental LAN exposure.
6. **Developer Compose, not a production appliance (§6.2):** public local database
   credentials and no application authentication are deliberate local defaults,
   not a security claim. OVA, OS/Raspberry Pi packages, GUI installer, chat UI,
   Croatian localization, admin flows, full multi-tenancy/auth, federation, cloud
   routing, model benchmarking, and production hardening are deferred to scoped
   follow-ups. No NGI deliverable or pilot commitment is inferred.

## Human confirmation requested

These choices do not block an initial skeleton, but should be confirmed before
the next feature increment:

- Keep the proposed `api/core/domain/mcp` layout and defer business schema depth
  until tenancy/auth requirements and migrations are agreed.
- Keep separate stdio MCP stub processes and the provisional argument/default
  choices in [MCP stubs](mcp-stubs.md); decide real integration/transport priorities.
- Confirm the deferred frontend and AI/provider stack rather than treating the
  historical Chat UI/EuroLLM/Mem0/RouteLLM selections as binding.
- Accept the explicitly development-only Compose baseline; commission separate
  production defaults and deployment work before exposure or sensitive data.
