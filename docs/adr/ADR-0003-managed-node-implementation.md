# ADR-0003: Implement the approved restricted managed node

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.

## Context

The requester explicitly approved ADR-0002 on 2026-10-26. Its document remains
unchanged on the separate design branch. The configuration additions need an
implementation record under the repository's contribution rules.

## Decision

Implement ADR-0002 without expanding the skeleton's application scope.
Separate independent state bootstrap, retained storage and disposable compute.
Keep secrets outside Terraform and GitHub. Gate managed Compose through systemd.
Require an approved immutable source commit and operator authorization for spend.
Accept the approved standalone first-dev ceiling of EUR 27/month net; the shared
services, EU monitoring/mail and ten-hour runner assumptions remain unchanged.

## Consequences

Local Compose defaults remain unchanged. Paid cloud acceptance, real DNS-01,
backend cold recovery and 30-day PITR measurements require operator execution;
offline checks do not certify them. Software and configuration remain
AGPL-3.0-or-later; documentation remains CC BY-SA 4.0 with Infosit attribution.
