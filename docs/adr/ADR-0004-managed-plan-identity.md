# ADR-0004: Isolate read-only planning credentials

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.

## Context

Protected infrastructure plans refresh bucket configuration and policy.
They must not receive node write keys, recovery deletion keys, or owner keys.
Retained disks must also match the node's actual provider location.

## Decision

Require an independent `plan_principal` for each retained root.
Allow only the bucket metadata reads used by the pinned AWS provider.
Explicitly deny object reads and mutations, including policy changes.
Keep the planning credential in a separate credentials project.
Compare the returned disk location with the node location before provisioning.

## Consequences

Private retained inputs need the public planning-key ARN.
No additional cloud resources or spending authorization are introduced.
Provider and policy contract tests run without cloud credentials or paid resources.
Live S3 interoperability remains an operator acceptance requirement.
