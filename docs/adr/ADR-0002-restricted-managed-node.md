# ADR-0002: Restricted Hetzner managed BATO node

Copyright (C) 2026 Infosit d.o.o., the implementer of BATO.
Documentation: CC BY-SA 4.0. Status: **proposed; human approval required**.

## Context

Infosit will operate one portable Compose node per tenant/environment.
The requester selected German Hetzner hosting, x86 CPU, separate PostgreSQL
storage, isolated dev/prod, DNS-01, external secrets, encrypted physical
backups, and trusted EU planning. This ADR proposes the remaining choices.
**Design approval does not authorize implementation or cloud expenditure.**

Baseline: `factory/configurable-api-log-format`, commit
`15c534f4bb7ec7e1ce88fb82b35dd685bfff8509`. `compose.yaml:1` runs PostgreSQL
16/pgvector and a source-built API with development passwords.
`src/bato/api/app.py:76` connects through Psycopg/libpq.
The API is unauthenticated. Only allowlisted skeleton access is approved;
the other restrictions in `docs/development.md:74` remain. Even an environment
named `prod` must contain **no sensitive data**. This is not production readiness.

## Decision

### Node, DNS and ingress

- Use Debian 12, Docker/Compose, location `fsn1` (alternative `nbg1`) [1].
  Dev: CX23, 2 vCPU/4 GB, 20 GB PostgreSQL volume.
  Prod: CX33, 4 vCPU/8 GB, 100 GB volume.
  Fail on unavailable capacity; never silently substitute ARM, country or price.
- Isolate tenant/environment resources, credentials and state. An operator
  supplies project-scoped API tokens; account/project setup is a bootstrap
  prerequisite, not an invented Terraform project resource. Provision a VM,
  volume, private network, firewall, DNS records and private backup bucket.
  Use a managed Compose override; do not alter local development defaults.
- Publish only TCP 443 to tenant/operator CIDRs and TCP 22 to admin CIDRs.
  Enforce equivalent IPv4/IPv6 allowlists in cloud and host firewalls. Permit
  essential ICMPv6/NDP and related replies; close 80/5432/8000 [2].
  Keep PostgreSQL on the Compose network and API 8000 on loopback.
  Traefik uses host networking/file routing to that loopback port: no Docker
  socket, dashboard or public DB. Permit outbound HTTPS, DNS and time sync.
- Choose Traefik DNS-01, lego provider `hetzner`, current **Cloud DNS API**,
  `HETZNER_API_TOKEN_FILE`. Pin a supported Traefik image by digest with
  lego >=4.27; Hetzner documents support since Traefik 3.5.4 [3].
  Terraform owns A/AAAA; Traefik owns challenge TXT. Use a dedicated delegated
  DNS project/zone to constrain the project-scoped token. Persist private ACME
  material. A different DNS provider requires its documented compatible
  integration; a variable alone does not implement every provider.

### Independent state and secrets

- Choose Terraform's `pg` backend: its advisory locking is documented [4].
  Independently bootstrap a German CX23 state VM and 10 GB volume in an
  operator project. Put PostgreSQL data/WAL/temp files on LUKS2; disable
  swap/core dumps. Use operator-CA TLS `verify-full`, a separate database/login
  per tenant/environment and separate schemas per root. Backend 5432 is
  private-network/verified-SSH-tunnel only, including EU runner access.
  Nodes receive no backend credentials. Backend loss blocks changes, not nodes.
- Future `infra/bootstrap/` uses temporary local state on an encrypted EU
  operator workstation's tmpfs, **not the backend it creates**. An SSH bootstrap
  installs/configures PostgreSQL; inject LUKS keys, CA and credentials through
  stdin, never cloud-init. Keep SOPS/age-encrypted state checkpoints after each
  operation and recover interrupted operations from inventory/import. Store
  checkpoints in two operator-controlled EU locations. The bootstrap root and
  runbook must reproduce the service without a pre-existing server.
- Back up backend PostgreSQL with the encrypted pgBackRest/WAL method below;
  export encrypted state after each successful infrastructure change.
  Keep CA recovery material, LUKS headers/keys, age identities and backup keys
  outside node/backend lifecycles. Restore backend first, then compare state
  lineage/serial with cloud inventory before planning. Operator unlock after
  a state-host reboot is deliberate. No unattended backend HA is promised.
  Renew backend TLS before expiry; rotate logins/LUKS keyslots with overlapping
  old/new access and a successful recovery test before retiring old material.
- Choose **SOPS/age plus operator SSH injection**, not a proprietary vault [5].
  Keep encrypted per-environment bundles outside this public repo on EU storage.
  Decrypt on the EU workstation; stream over host-key-verified SSH to an atomic
  installer. Persist root-controlled, mode-0400 service-readable files for DB,
  DNS, object-store and backup secrets; retain them across restarts/updates.
  Recover by reinjection. Cloud/root administrators can access live secrets.
- Terraform must never generate/read node secrets through resources, data,
  `external`, provisioners or templates. User data contains non-secret bootstrap
  only. Supply provider/backend credentials through private environment/files,
  not public tfvars, secret command arguments, `-backend-config`, outputs or
  CI artifacts. Backend uses password-free `PG_CONN_STR` + `PGPASSFILE` [4,6].
  The managed override removes development passwords: PostgreSQL uses
  `POSTGRES_PASSWORD_FILE`; API uses password-free `BATO_DATABASE_URL` plus
  `PGPASSFILE` readable by UID 10001 [6], with a separate non-superuser role.
- Gate **every** Compose start with systemd checks for expected device identity,
  mounted filesystem, approved release SHA and secret permissions. Disable
  container auto-start bypasses. Bind-mount PGDATA with directory auto-creation
  disabled; never fall back to a named/root-disk volume. Only explicit first
  installation may format a blank disk or initialize an empty database.
- Rotate DB credentials in maintenance: stop API, update role via local DB
  session with secret stdin, atomically replace passfile, start/check readiness;
  retain old credential until acceptance for controlled rollback. Inject/test/
  revoke DNS/object credentials. Rewrap SOPS recipients on operator changes.
  Compromise requires key rotation. Backup cipher rotation creates a new
  repository/key epoch; retain old keys for every retained backup. Never log
  secret SQL/input or enable shell tracing.

### Backup, recovery and lifecycle contract

- Extend the pinned PG16/pgvector image with pinned pgBackRest. PostgreSQL runs
  `archive-push`. Take weekly physical full and daily differential backups;
  use `archive_mode=on`, `wal_level=replica`, `archive_timeout=300s`, synchronous
  WAL archiving and no queue limit that drops WAL [7,8].
- Store backups off-node in `nbg1` for `fsn1` nodes (or vice versa).
  Use private Hetzner S3, TLS verification and pgBackRest client-side
  `aes-256-cbc` encryption with separate repository passphrases/offline EU copies.
  Hetzner objects have **no default at-rest encryption**; available SSE-C is
  not a substitute for this client-side encryption [9].
- Maintain **at least 30 days of PITR**, including the older full backup/WAL
  needed at the boundary: time-based 30-day full retention, no premature WAL
  expiry. Disable automatic node expiry; a separate off-node retention
  principal expires old chains. Node policy denies delete/cross-tenant access.
  Prove pgBackRest and Hetzner policies interoperate before accepting backups.
- Run a five-minute off-node check/committed heartbeat on the state service.
  Alert an EU operator mail destination for archive lag >15 minutes, any archive
  failure, no backup success for 26 hours, missing heartbeat, >80% data/WAL disk
  usage or TLS expiry <21 days. One-hour RPO depends on healthy archiving and
  operator response. Existing EU mail delivery is an explicit cost assumption.
- Restore to an isolated replacement VM/volume: inject keys; restore physical
  backup with the same PG major/pgvector/pgBackRest versions; replay WAL to the
  chosen time; verify transaction marker, vector query and readiness; switch
  DNS. Retain old disk until acceptance. Test before service acceptance and
  quarterly. **Four-hour RTO is a measured target**, from incident declaration
  through restored HTTPS including operator/backend recovery, not a guarantee.
  An existing always-on EU operations host runs Prometheus/Alertmanager to
  check the state service's heartbeat independently and notify on its loss.
- Separate future `infra/retained/` storage from `infra/node/` compute state.
  Ordinary node destroy removes compute/network/DNS, **not prod disks,
  buckets/objects or recovery keys**. Use Terraform/provider storage protection.
  On decommission, stop expiry and freeze the complete last restore chain.
  Retention charges continue. Purge requires separate operator approval naming
  the exact environment/resources, removal of protection, verified deletion
  including object versions, then retirement of obsolete keys [10].
- Require an explicitly user-approved full 40-character `source_commit`;
  logging HEAD is **not** an approved deployment SHA. Never choose `latest` or
  a branch. Verify fetched HEAD; build committed lockfile/digest-pinned bases
  into a new release directory and record image IDs. Keep previous images.
  Updates take a verified fresh backup, build before downtime, recreate and
  check readiness/HTTPS. No VM replacement for application updates. Roll back
  images/config only with compatible data; otherwise stop and restore.
  No schema downgrade or loss-free data rollback is promised.
- Infosit owns monitoring, security updates and restore drills. Apply daily OS
  security updates without automatic reboot; test/schedule reboots and pinned
  image updates in an agreed window, then recheck mounts/secrets/TLS/WAL.
  Future reviewed tags map to immutable commits/digest-pinned published images;
  this task does not create that release process.

### Public inputs, CI and residency

- Future Terraform inputs cover tenant/environment labels, project/zone
  references, location/SKU, volume size, source SHA, FQDN/DNS provider,
  admin/HTTPS CIDRs, public SSH key, bucket/endpoints and operator contact.
  Examples: `node_fqdn = "tenant.dev.bato.example.org"`,
  `dns_provider = "hetzner"`, `tenant-example`, `192.0.2.0/24`,
  `198.51.100.0/24`, `2001:db8::/32`, mock-only IDs/SHA/public key.
  No real ownership identifiers or secrets are required for review.
  Reject empty allowlists and `0.0.0.0/0`/`::/0`. Backend configuration uses
  private environment/files, not Terraform variable interpolation.
- All PRs run credential-free `terraform fmt -check -recursive`,
  `terraform init -backend=false` and `terraform validate` per root.
  Validate does not test example values: separately run
  `terraform test -var-file=examples/dev.tfvars` and prod equivalent with
  mocked providers/plan-only tests and no backend/cloud calls [11].
  Do not pass `-var-file` to `terraform validate`.
- Plans require manual dispatch/operator approval of an **exact trusted SHA**
  on a single-job ephemeral German runner with isolated network, environment-
  scoped read-only cloud credentials and minimum backend lock/read privileges.
  Never run PR/fork code there; no `pull_request_target` checkout or prod CI apply.
  Capture all raw stdout/stderr/plans/state in an encrypted access-controlled
  EU review store, not GitHub logs/artifacts/caches. Publish sanitized status
  only. Disable tracing/provider debug; destroy the runner after each job.
  CI never receives node-secret bundles.
- **Approval assumption:** tenant data, secrets, backups, state and raw plans
  stay on EU compute/storage. GitHub's public source/CI control plane and
  DNS/ACME certificate transparency expose code, job metadata and certificate
  names internationally. Do not claim absolute all-metadata-in-EU residency.
  Use nonsensitive public labels.

### Cost estimate for approval

Checked **2026-10-26**; EUR/month **excluding VAT**, estimates not bills/caps [12].

- Dev: CX23 €5.49 + IPv4 €0.50 + 20 GB at budget rate €0.0572/GB-month
  = **€7.13**. Prod: CX33 €8.49 + IPv4 €0.50 + 100 GB = **€14.71**.
  IPv6/firewalls/private network add no separate estimated charge.
- Shared: state CX23/IPv4/10 GB **€6.56**; object-storage account minimum
  **€6.49**, including combined backend/node backups within the hourly-accruing
  ~1 TB storage/egress allowance [9,12]; EU runner 10 hours/month **€0.10**.
  Full-month runner at this SKU/IP costs **€5.99**, not zero.
- One dev/prod pair splits shared €13.15: **dev €13.71, prod €21.29,
  pair €35.00**. Full-month runner: dev €16.66/prod €24.23.
  First tenant with dev alone pays **€20.29** normally, **€26.18** with a
  full-month runner: the latter **exceeds €25 dev**. Prod stays below €60.
- **Approval assumptions:** net infrastructure ceilings; shared control services;
  runner limited operationally to 10 hours/month; existing EU operator mail
  and monitoring host. Without that host, add a separate CX23/IPv4 (€5.99);
  a standalone dev then reaches €26.28 and needs a budget decision.
  At illustrative 19% VAT, normal pair €41.65 (dev €16.31/prod €25.33).
  Domain registration, labour/on-call, exceptional restores, overlapping
  recovery VMs and indefinitely retained decommission data are excluded.
- Assume dev <=10 GB/prod <=50 GB used, low change rate and combined retained
  backup/WAL <1 TB. Extra object storage is €0.0087/TB-hour (~€6.47/TB in a
  31-day month); excess object egress is €1/TB [12]. Intra-EU-central traffic
  is free [9]. Growth, excess egress or unavailable CX capacity requires
  a new estimate; alert at 80% quota/budget, never delete recovery data to cap
  cost. Static volume calculator still shows €0.044; live catalogue carries
  €0.0572. Budget conservatively at the latter; confirm order price before spend.

## Consequences

- **State trade-off:** PostgreSQL has documented locks; Hetzner S3 conditional-
  write lockfile semantics were not established. S3 would save a VM but needs
  locking/encryption/recovery proof before a later ADR selects it. PostgreSQL
  adds maintenance, manual unlock and a shared change-time failure dependency.
- **Secrets trade-off:** SOPS/age avoids an always-on vault/proprietary service,
  but requires operator rotation and offline-key custody. No automatic leasing.
- **Topology trade-off:** one x86 Compose VM lowers cost and enables own-hardware
  migration, but has restore downtime, not HA. Managed DB/Kubernetes add cost/
  dependency; server snapshots do not back up attached volumes [10].
- Out of scope: app authentication/sensitive data, business schema/migrations,
  HA, inference/chat/memory/MCP deployment, ARM, release publishing and GPU.
  A later GPU design must select real EU capacity, runtime/drivers, model
  licenses and budget; do not add a nonfunctional GPU flag.
- After approval, implementation adds `infra/` roots/runbooks, managed Compose,
  CI and `docs/deployment-cloud.md`. Software/config stays AGPL-3.0-or-later;
  docs stay CC BY-SA 4.0 with Infosit attribution; third-party terms stay intact.

## Validation criteria

**Required future acceptance checks; none is claimed by this docs-only PR.**

1. Run fmt/init/validate above and offline mock tests `public_examples`,
   `reject_open_ingress`, `reject_non_german_location`, `separate_environments`
   and `retain_storage`. Both example tfvars pass without real IDs/secrets/APIs.
2. EU lab `backend_lock_and_restore`: second concurrent writer blocks; killed
   holder releases lock; bad TLS/credentials fail; independent recovery restores
   backend/state lineage/serial. Include interrupted bootstrap and cold key access.
3. `secret_and_mount_gate`: missing/wrong/unmounted disk or secrets prevents DB
   creation; marker survives reboot/update. Scan state/plan/user data/arguments/
   Compose config/inspect/logs for a synthetic canary password. Exercise credential
   rotation, old-backup decryption and gate enforcement before Docker auto-start.
4. Private-value operator acceptance: allowed/denied IPv4/IPv6 443/22, closed
   80/5432/8000, correct HTTPS/DNS-01 issue/renewal with port 80 closed,
   readiness/vector query. **Never claim ACME success for `example.org`.**
5. `backup_pitr_and_destroy`: recover a marker <=1 hour before simulated loss
   in <4 hours, including backend failure/key recovery; prove 30-day boundary
   PITR, ciphertext, cross-tenant/delete denials, prod-destroy retention, frozen
   decommission chain and separately approved purge. Storage outage must alert
   the operator within 15 minutes; test monitor/backend dead-man delivery too.
6. `trusted_plan_boundary` proves untrusted code cannot get credentials/runner
   access and raw output stays EU-only. `update_and_rollback` proves approved-SHA
   selection, failed-build isolation and refusal of incompatible data rollback.
7. Before paid service acceptance, record actual order prices/SKU availability,
   named on-call/maintenance coverage, alert delivery and measured restore time.
   These are operational gates, **not prerequisites for public design approval**.

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
