# ADR-0002: Restricted Hetzner managed BATO node

Copyright (C) 2026 Infosit d.o.o., the implementer of BATO.
Documentation: CC BY-SA 4.0. Status: **proposed; human approval required**.

## Context

Infosit will operate isolated tenant/dev/prod Compose nodes in Germany.
The approved scope is an allowlisted skeleton, **not production application
authentication or sensitive data**, including in `prod`.
Baseline `factory/configurable-api-log-format` at `15c534f` runs PG16/pgvector
and an unauthenticated API (`compose.yaml:1`, `docs/development.md:74`).
This PR contains no implementation; implementation starts only after explicit
design approval. Cloud expenditure/apply requires separate operator authorization.

## Decision

### Node, DNS and ingress

- Use Debian 12/x86/Compose in `fsn1`, alternatively `nbg1` [1].
  Dev: CX23 (2 vCPU/4 GB), 20 GB PostgreSQL volume.
  Prod: CX33 (4 vCPU/8 GB), 100 GB volume. Fail on unavailable capacity.
- Provision isolated VM/volume/network/firewall/DNS/bucket/state per environment.
  Operator-created accounts/projects/tokens are prerequisites. Add a managed
  Compose override; preserve local defaults. PostgreSQL stays private;
  API stays on loopback. Traefik uses host-network/file routing, no Docker socket.
- Cloud and host firewalls allow TCP 443 from tenant/operator CIDRs and 22 from
  admin CIDRs, equally for IPv4/IPv6; close 80/5432/8000. Permit essential
  ICMPv6/NDP/replies and outbound HTTPS/DNS/time sync [2].
- Use Traefik DNS-01, lego `hetzner`/current Cloud DNS,
  `HETZNER_API_TOKEN_FILE`, persisted private ACME material, and a digest-pinned
  supported image with lego >=4.27 (Traefik support since 3.5.4) [3].
  Terraform owns A/AAAA; Traefik owns TXT. Scope tokens through a dedicated
  delegated DNS project/zone. Other providers need documented compatible adapters.

### Independent state and secrets

- Choose Terraform `pg` advisory locking [4]: independent German CX23/10 GB
  state service, LUKS2 for PostgreSQL data/WAL/temp, no swap/core dumps,
  operator-CA TLS `verify-full`, database/login per tenant/environment and
  schema per root. Backend 5432 is private-network/verified-SSH-tunnel only;
  nodes receive no backend access.
- `infra/bootstrap/` reproducibly creates that service using temporary local
  state on an encrypted EU workstation's tmpfs, **not its own backend**.
  SSH configuration receives keys/credentials through stdin, never cloud-init.
  Keep SOPS/age-encrypted checkpoints in two operator-controlled EU locations;
  recover interrupted operations through inventory/import.
- Back up backend PostgreSQL as below; export encrypted state after changes.
  Keep CA/LUKS headers/keys, age identities and backup keys independently.
  Restore backend first; reconcile lineage/serial/inventory before planning.
  Reboots require operator unlock. Rotate TLS/logins/LUKS keys with overlapping
  access and recovery verification. Backend loss blocks changes, not nodes.
- Choose OSS SOPS/age [5]: encrypted per-environment bundles outside GitHub,
  decrypted on an EU workstation and streamed over verified SSH to atomic,
  persistent root-controlled, mode-0400 service-readable files.
  Restart/update retains secrets; recovery reinjects them.
  Terraform never reads/generates node secrets through resources/data/`external`/
  provisioners/templates. No secrets in user data, arguments, outputs or CI.
- Provider/backend credentials use private environment/files, never public tfvars
  or secret `-backend-config`. Backend: password-free `PG_CONN_STR`/`PGPASSFILE`.
  Replace development passwords with `POSTGRES_PASSWORD_FILE` and API
  password-free `BATO_DATABASE_URL`/`PGPASSFILE`, UID 10001, non-superuser [6].
- Systemd gates every Compose start on device/mount identity, approved SHA and
  secrets; prevent Docker restart bypasses. Bind PGDATA without auto-creation.
  Missing mounts/secrets fail closed; only explicit first-install initializes.
- Rotate DB password/passfile together during maintenance; inject/test/revoke
  DNS/object credentials and rewrap departing SOPS recipients. Never log secrets.
  Backup-key rotation creates a new repository epoch; preserve old recovery keys.

### Backup, recovery and lifecycle contract

- Add pinned pgBackRest to PG16/pgvector: weekly physical full/daily differential
  backups, synchronous WAL `archive-push`, `archive_mode=on`,
  `wal_level=replica`, `archive_timeout=300s`; never drop queued WAL [7,8].
- Private Hetzner S3 in the other German location holds TLS-verified,
  client-side `aes-256-cbc` encrypted repositories with independent passphrases/
  offline EU keys. Hetzner has **no default object encryption**; SSE-C is optional [9].
- Preserve >=30-day PITR, including the older boundary full/WAL chain.
  Disable node expiry; off-node retention principal expires old chains.
  Node policy denies delete/cross-tenant access.
- State-service checks/committed heartbeat run every five minutes; alert EU
  operators for archive lag >15 minutes/failure, missing heartbeat, backup age
  >26 hours, disk >80%, TLS expiry <21 days. Independent EU
  Prometheus/Alertmanager monitors service loss.
- Target **one-hour RPO/four-hour RTO**, not guarantees: RTO includes operator/
  backend recovery through restored HTTPS. Restore physical backup/WAL with
  matching PG/pgvector/pgBackRest versions to isolated replacement storage;
  verify marker/vector/readiness before DNS cutover. Test initially/quarterly.
- Separate `infra/retained/` from `infra/node/` state. Ordinary destroy retains
  prod disk/bucket/objects/keys with Terraform/provider protection.
  Decommission freezes the restore chain/expiry; charges continue.
  Separate named-resource purge approval precedes verified deletion/key retirement [10].
- Require user-approved full 40-character `source_commit`, never branch/`latest`;
  logging HEAD is not approved. Verify HEAD, build lockfile/digest-pinned bases,
  retain previous images/config. Update after verified backup/build, then check
  HTTPS/readiness. Compatible image/config rollback only; otherwise restore.
  No schema downgrade/loss-free data rollback promise.
- Infosit owns daily OS security updates, scheduled reboots/image updates,
  monitoring and drills. Later tags map to commits/digests; no publishing process now.

### Public inputs, CI and residency

- All identifiers/settings are variables: tenant/environment, project/zone,
  location/SKU/storage/SHA, FQDN/provider/CIDRs, SSH public key, bucket/endpoints,
  contact. Examples use `node_fqdn = "tenant.dev.bato.example.org"`,
  `dns_provider = "hetzner"`, RFC 5737 IPv4/`2001:db8::/32` and mock IDs/keys.
  Reject empty/global allowlists. Real identifiers are unnecessary for review.
- All PRs: credential-free `terraform fmt -check -recursive`,
  `terraform init -backend=false`, `terraform validate` per root.
  Separately test dev/prod examples with `terraform test -var-file=examples/dev.tfvars`
  (prod equivalent), mocked providers/plan-only tests, no backend/API calls [11].
  Validate does not load tfvars; do not give it `-var-file`.
- Manually approve/dispatch exact reviewed SHA plans on single-job ephemeral
  German runners: isolated network, environment-scoped read-only cloud
  credentials/minimum backend lock-read access. **Never run unapproved/untrusted
  PR or fork code**; no `pull_request_target` checkout or prod CI apply.
  Raw stdout/stderr/state/plans stay encrypted/access-controlled in EU storage,
  not GitHub logs/artifacts/caches. Publish sanitized status only; disable debug/
  tracing, destroy runners, never inject node bundles.
- **Approval assumption:** tenant data/secrets/backups/state/plans stay EU;
  GitHub control-plane and public DNS/ACME transparency expose code/job metadata/
  certificate names internationally. No absolute all-metadata-EU guarantee.

### Cost estimate for approval

Checked **2026-10-26**; EUR/month **excluding VAT**, estimates not bills/caps [12].

- Dev: €5.49 VM + €0.50 IPv4 + 20 GB × €0.0572 = **€7.13**.
  Prod: €8.49 + €0.50 + 100 GB × €0.0572 = **€14.71**.
- Shared: state VM/IP/10 GB **€6.56**, object-account minimum **€6.49**
  (~1 TB hourly-accruing storage/egress), 10 runner hours **€0.10**.
  IPv6/network/firewall: no separate estimated charge.
- Pair splitting €13.15 overhead: **dev €13.71/prod €21.29; total €35.00**.
  Full-month runner (€5.99): dev €16.66/prod €24.23.
  Dev alone: €20.29 normally; €26.18 with full-month runner **exceeds €25**.
- **Approval assumptions:** net ceilings, shared services, 10 runner hours,
  existing EU mail/monitor. Missing monitor adds €5.99: standalone dev €26.28.
  Prod remains below €60. At example 19% VAT, normal pair €41.65.
  Excludes registration/labour/on-call, exceptional restores/overlap and
  indefinite decommission retention.
- Assume <=10/50 GB dev/prod used, low churn, backups/WAL <1 TB.
  Extra storage €0.0087/TB-hour; object egress €1/TB, EU-central traffic free.
  Alert at 80% quota/budget; growth requires re-estimation, not backup deletion.
  Static volume calculator €0.044 conflicts with live catalogue €0.0572:
  budget latter; confirm order pricing before spend.

## Consequences

- PostgreSQL's proven locks cost maintenance/manual unlock; Hetzner S3
  conditional-write locking remains unverified. SOPS avoids a vault but needs
  operator custody/rotation; root administrators can read live secrets.
- Compose stays portable to own hardware; single-VM recovery replaces HA.
  Managed DB/Kubernetes add cost/dependency; snapshots exclude volumes [10].
- Exclude app authentication/sensitive data, migrations, HA, inference/chat/
  memory/MCP, ARM, release publishing and GPU. Later GPU work needs actual EU
  capacity/drivers/model-license/budget design, not a placeholder flag.
- Approved implementation adds `infra/`, managed Compose/CI and
  `docs/deployment-cloud.md`; preserve AGPL-3.0-or-later software,
  CC BY-SA 4.0 documentation and Infosit/third-party attribution.

## Validation criteria

**Required future acceptance checks; none is claimed by this docs-only PR.**

1. Offline `public_examples`: fmt/init/validate plus mocked dev/prod tfvars
   tests; reject open ingress/non-German placement; prove environment isolation.
2. EU-lab `backend_lock_and_restore`: concurrent lock exclusion/release,
   invalid-TLS rejection, interrupted-bootstrap/cold-key recovery and serial match.
3. `secret_and_mount_gate`: missing/wrong mounts/secrets prevent initialization;
   reboot/update preserves markers; canary-secret scan covers state/plan/user
   data/arguments/Compose inspect/logs. Verify rotation/old-key restores.
4. Operator `network_tls`: IPv4/IPv6 allow/deny checks, closed private ports,
   real DNS-01 renewal/readiness/vector query. No ACME claim for example domains.
5. `backup_pitr_and_destroy`: <=1-hour marker loss/<4-hour recovery including
   backend loss; 30-day boundary PITR, ciphertext/policies, retention/purge.
   Storage/monitor failures must deliver operator alerts within 15 minutes.
6. `trusted_plan_boundary` and `update_and_rollback`: credential isolation,
   EU-only raw outputs, exact-SHA selection, failed-build/incompatible-data refusal.
7. Before paid acceptance, record actual prices/capacity, on-call coverage and
   measured recovery. These operational gates do not block public design approval.

## Evidence

Official references checked 2026-10-26:

1. [Hetzner locations](https://docs.hetzner.com/cloud/general/locations/).
2. [Firewall behavior/exceptions](https://docs.hetzner.com/cloud/firewalls/faq/).
3. [Cloud DNS integrations/token scope](https://docs.hetzner.com/networking/dns/migration-to-hetzner-console/features-and-differences/);
   [lego file credentials](https://go-acme.github.io/lego/dns/hetzner/);
   [Traefik DNS-01](https://doc.traefik.io/traefik/reference/install-configuration/tls/certificate-resolvers/acme/).
4. [Terraform pg advisory locking/credentials](https://developer.hashicorp.com/terraform/language/backend/pg).
5. [SOPS/age](https://getsops.io/docs/).
6. [libpq credential files](https://www.postgresql.org/docs/16/libpq-envars.html).
7. [PostgreSQL continuous archiving](https://www.postgresql.org/docs/16/continuous-archiving.html).
8. [pgBackRest physical/PITR/encryption](https://pgbackrest.org/user-guide.html);
   [retention/archive settings](https://pgbackrest.org/configuration.html).
9. [Object storage locations/no default encryption](https://docs.hetzner.com/storage/object-storage/faq/general/);
   [account-wide quota](https://docs.hetzner.com/storage/object-storage/overview/).
10. [Snapshots exclude volumes](https://docs.hetzner.com/cloud/servers/backups-snapshots/faq/);
    [volume lifecycle](https://docs.hetzner.com/cloud/volumes/overview/).
11. [Terraform provider mocks](https://developer.hashicorp.com/terraform/language/tests/mocking).
12. [June 2026 server prices](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/);
    [live catalogue](https://www.hetzner.com/_resources/app/data/app/live_data_prices.json)
    (`CLOUD_132` CX23, `CLOUD_133` CX33, `CLOUD_21` IPv4, `CLOUD_23` volume rate);
    [static volume calculator](https://www.hetzner.com/cloud/block-storage/);
    [object-storage prices](https://www.hetzner.com/storage/object-storage/).
