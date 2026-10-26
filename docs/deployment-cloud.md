# Restricted managed BATO node

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.
Software/configuration: AGPL-3.0-or-later.

This implements the explicitly approved [ADR-0002](adr/ADR-0002-restricted-managed-node.md)
and records implementation in [ADR-0003](adr/ADR-0003-managed-node-implementation.md).
Read-only planning identity isolation is recorded in
[ADR-0004](adr/ADR-0004-managed-plan-identity.md).
It deploys the **unauthenticated health/status skeleton only**. Even `prod` must
remain allowlisted and contain no sensitive application data. It adds no
application authentication, inference, UI, MCP integration or release publishing.
No cloud apply or real ACME issuance forms part of repository verification.

## Layout and prerequisites

- `infra/bootstrap`: independently protected German state VM, LUKS data disk,
  private control network and separate cross-German backup bucket. Local backend.
- `infra/retained`: one tenant/environment's disk and encrypted-backup bucket.
  Independent PostgreSQL remote state. Protected from ordinary destruction.
- `infra/node`: disposable compute/network/cloud firewall/A/AAAA and attachment
  of the retained disk. It has no disk/bucket ownership and no secret inputs.
- `deploy/managed`: Compose override, pinned backup image and systemd gates.
  Root `compose.yaml`, development credentials and developer workflow stay unchanged.

Use an encrypted EU operator workstation with swap disabled, Terraform **1.13.5**,
SOPS/age, OpenSSH, AWS CLI v2 and Docker Compose **2.24.4+**. Install official signed
packages/releases; do not curl-pipe installers. Provider locks pin hcloud 1.70.2
and AWS 6.70.0. The AWS provider talks only to Hetzner's S3 endpoint, never AWS.
Docker is required for the public offline Compose test, not for Terraform plans.
Infosit must approve the full source SHA and separately authorize all expenditure.

Create isolated Hetzner projects, delegated DNS zone and operator credentials.
Use separate S3 **credentials projects** from the bucket-owner project. Per-key
ARNs are public identifiers, not secret keys. Do not put any real identifiers,
domains, credentials, tfvars, plans or SOPS bundles into this public repository.
Replace example IDs/keys/domains and RFC 5737/`2001:db8` addresses privately.
Hetzner live private networks need operator-chosen RFC1918 subnets; documentation
networks are intentionally mock-only. Reserve distinct subnets for each environment.
An example `source_commit` of repeated digits is **not approval to deploy**.
Example.org cannot receive a real ACME certificate.

CPU baseline is Debian 12/x86, CX23 dev/20 GB, CX33 prod/100 GB, `fsn1` or `nbg1`.
Select and verify a Debian 12 x86 image ID before spending. Fail on missing SKU
capacity; do not silently switch architecture/location. A later GPU extension
needs EU capacity, driver/runtime, model licence and budget review; no GPU flag
or paid GPU resource is implemented.

## Public verification

With Terraform on PATH, run `bash infra/ci/offline.sh`. It performs recursive fmt,
backend-disabled init and validate for all roots, then separately loads each dev
and prod tfvars through mocked **plan-only** tests. `validate` does not accept or
load a var-file. No cloud/backend credentials or API calls are required.
Run the README's Python checks and `docker compose up --build --wait`, followed by
`uv run pytest -m deployment`. The new physical test uses synthetic file secrets,
PG16/pgvector and AES-encrypted pgBackRest backup/WAL on local POSIX storage.
It restores to a timestamp into separate storage and checks included/excluded
markers, pgvector and inspect/log canaries. It is **not Hetzner S3 certification,
30-day history, cold-backend recovery or a measured cloud RTO**.

## Bootstrap and backend custody

Follow [independent state bootstrap and recovery](../infra/runbooks/state.md)
first. Nodes never join the state control network and receive no state credential.
Each tenant/environment gets its own database/login; each root gets its own schema.
Use only the default Terraform workspace; do not use workspaces for tenant isolation.
Never copy a dev state or disk ID into prod. Native PostgreSQL advisory locks
serialize operations. Backend loss blocks Terraform, not running nodes.

Backend/provider credentials belong in restricted private environment/files.
Use a password-free `PG_CONN_STR`, `sslmode=verify-full`, independently held CA
and mode-0400 `PGPASSFILE`. Do not pass credentials with `-backend-config`.
Use a verified SSH tunnel to the state's loopback-only 5432; never open 5432
publicly. Provider plan credentials are read-only; an operator apply uses separately
authorized credentials. Terraform stores public resource metadata, not node secrets.

## Provision one environment

1. Obtain spending authorization. Complete the state/bootstrap runbook. Copy the
   appropriate examples to private operator storage and replace all mock inputs.
2. Select the tenant/environment backend database and `PG_SCHEMA_NAME`, for
   example `example_dev_retained`. Initialize `infra/retained`, plan privately,
   review its exact plan, then operator-apply it. Export state after every change
   to tmpfs and run `infra/scripts/checkpoint.sh` for two independent EU copies.
3. Transfer `volume_id`/`volume_name` into private node inputs. Select the node
   root's **different** backend schema, for example `example_dev_node`.
   Initialize, privately plan/review, then operator-apply `infra/node`.
4. Save `terraform -chdir=infra/node output -json operator_manifest` in private
   operator storage. The manifest contains only public configuration. Verify the
   disk ID, environment, approved SHA, SSH host fingerprint and cloud inventory.
   Cloud-init/user-data/provisioners are deliberately absent.
5. On the node, check out the explicitly approved SHA, verify a clean tree,
   and run `bash infra/scripts/install-host.sh /path/to/checkout "$APPROVED_SHA"`
   as the authorized root operator. This installs Docker from its fingerprint-
   checked official apt key, systemd units and operator scripts. It disables
   swap/core dumps; review existing host settings before using on owned hardware.
6. Stream the manifest to `python3 /usr/local/lib/bato/node.py render` over verified
   SSH. Enable/start `bato-firewall.service` before any application start. Keep
   a second verified operator session open while testing ingress.
7. **New blank disk only:** run `node.py first-disk`. It refuses existing signatures.
   This is the sole formatting path. For an existing disk, run `node.py mount`;
   it never formats or replaces its `.bato-volume.json` identity marker.
8. Inject the SOPS bundle as below. Stage with `node.py stage --source /path/to/checkout
   --approved-commit "$APPROVED_SHA"`. Build completion records exact local image
   IDs; failed builds have no activation receipt. Images/bases and uv lockfile are
   pinned. Run `node.py activate --approved-commit "$APPROVED_SHA"`.
9. **New PGDATA only:** run `node.py initialize`. It refuses an existing directory,
   creates the non-superuser API login and vector extension, then requires a
   successful encrypted full backup before stopping. Do not erase an interrupted
   initialization; investigate it or restore onto replacement storage.
10. Enable/start `bato-node.service`, `bato-backup.timer`, `bato-monitor.timer`.
    Test HTTPS/readiness, backup and EU monitoring delivery before acceptance.

`node.py` above abbreviates `python3 /usr/local/lib/bato/node.py`.
Only root/operator systemd may control Docker; do not give tenants Docker access.
All services use `restart: "no"`. Every systemd start/restart invokes the mount,
disk-marker, source, image-receipt, PG_VERSION and mode/ownership secret gates.
No Docker autostart restores containers around those gates. Leave Docker
live-restore disabled; stop BATO before Docker/OS maintenance.
The systemd mount binding stops the node if its data mount disappears.

## Secret injection and rotation

Keep one SOPS/age encrypted JSON bundle per tenant/environment outside GitHub.
Use independent random `db_password`, `api_password`, `dns_token`, complete
`pgbackrest_conf` and `monitor_curl` string fields. Start from
`deploy/managed/pgbackrest.conf.example`, replace its credentials, passphrase,
bucket, region and tenant path privately. Keep encryption passphrases offline in
two EU custodians' recovery stores. Node S3 keys must be in a different project
from the bucket and cannot be the owner/retention keys.

On the EU workstation, use:

```sh
sops decrypt --output-type json "$ENCRYPTED_BUNDLE" |
  ssh -o StrictHostKeyChecking=yes "$VERIFIED_NODE" \
    'python3 /usr/local/lib/bato/node.py inject'
```

The injector writes complete private generations and atomically switches `current`.
Files are mode 0400: database/backup UID 999, API passfile UID 10001, DNS/monitor
root. The API URL contains no password; libpq reads the escaped passfile.
PostgreSQL uses `POSTGRES_PASSWORD_FILE`. Bundles never enter Terraform, CI,
cloud-init, Compose password values, process arguments or output.
`monitor_curl` is a private curl config with an HTTPS EU heartbeat URL and any
monitor authentication; never use verbose/trace or insecure TLS options.
Root can read live secrets; this is not an application-secret vault.

Stop the node for database rotation. Inject the new generation, run `node.py
rotate-db` to recreate only the gated database and alter both roles from mounted
secret files without SQL password literals, then start through systemd and
verify API readiness. Merely changing `POSTGRES_PASSWORD_FILE` does **not** rotate
an initialized database. Keep the old encrypted bundle until verification.
Test/revoke old DNS/S3 keys; rewrap removed age recipients. Backup cipher-key
rotation starts a new repository epoch under a separately reviewed path/policy
change; retain old keys/repositories for their complete recovery windows.

## Network, monitoring, update and recovery

Both cloud and persistent `inet` host rules allow 443 only for tenant/operator
CIDRs and 22 only for admin CIDRs, IPv4 and IPv6. ICMP/NDP and established replies
remain allowed. Outbound DNS/HTTPS/time sync is permitted. Port 80 is closed;
DNS-01 uses the **current Cloud DNS** `hetzner` provider and
`HETZNER_API_TOKEN_FILE`. Traefik 3.7.16 includes a compatible lego version.
Use a dedicated delegated DNS project/zone; no socket provider or dashboard.
API 8000 stays loopback; DB 5432 has no published port. A dedicated `inet`
forward chain also blocks externally routed traffic into Docker bridges.
Verify the actual IPv4 **and** IPv6 allow/deny paths; examples prove no ACME result.

Every five minutes the monitor commits a heartbeat, checks archive lag/failure,
pgBackRest repository access, physical backup age <=26h, data disk <80%, valid
HTTPS and certificate lifetime >=21d. It sends success only after all checks.
Configure the independent existing EU Prometheus/Alertmanager/mail host to alert
on a missing success for ten minutes and probe node/state reachability separately
at least every five minutes. This catches a dead timer, VM, storage or monitor
process; test delivery within 15 minutes. State monitoring and full recovery are
covered by the [state runbook](../infra/runbooks/state.md).

For updates, stage a separately approved SHA without changing the current
release. Review schema compatibility explicitly. `activate --schema-compatible`
requires repository check plus a new full backup before stopping the old release.
It keeps the old release/images, previous SHA and a private manifest/proxy history.
Start through systemd, then check external HTTPS/readiness.
Do not prune old images/releases before a tested
rollback window. Compatible rollback stages/activates the previous retained
receipt/SHA with explicit compatibility approval and another verified backup.
While stopped, re-render the corresponding private history `node.json` if public
configuration also changed, reload the host firewall and then start through systemd.
If schema compatibility is unknown or false, stop and use physical restore;
image rollback is not data rollback. Never automatically erase data or downgrade.

Follow [backups, PITR, retention and destroy](../infra/runbooks/recovery.md).
Hetzner server snapshots/backups exclude attached volumes and are not data backups.
Follow [trusted plan runner operations](../infra/runbooks/plans.md) for plans.
No production apply job, fork secrets or `pull_request_target` exists.

## Residency and budget

Tenant data, secrets, backups, backend state and raw plans stay in EU-operated
storage. GitHub code/job/control-plane metadata and DNS/certificate-transparency
names are international; do not claim all metadata stays in Europe.

ADR-0002's 2026-10-26 net monthly estimates remain: dev EUR 7.13 direct,
prod EUR 14.71 direct, shared state/IP/disk EUR 6.56, object minimum EUR 6.49,
ten runner hours EUR 0.10. Pair total EUR 35.00; allocated dev EUR 13.71,
prod EUR 21.29. Standalone first dev EUR 20.29 normally; **up to EUR 27 net is
explicitly approved**. Assume existing EU monitor/mail, shared control services,
<=10/50 GB used dev/prod and low churn within the object-account quota.
The runner wrapper reserves 30-minute slots, refuses more than ten hours/month,
and relies on operator runner teardown. A full-month runner costs more; it is
not the approved operating model. Alert on 80% account quota/budget; re-estimate
growth, restore overlap and retained decommission charges instead of deleting
backup history. Confirm live pricing/capacity before spending; these are not bills.

Infosit owns daily security patching, scheduled reboots, pinned image/package
updates, CA/key custody, EU on-call coverage and initial/quarterly recovery drills.
Actual RPO <=1 hour and RTO <4 hours are **measured acceptance targets**, not
guarantees. Paid acceptance must record prices, reachability/TLS, lock/cold restore,
rotation, 30-day boundary PITR, policy/tool compatibility, notification delivery
and recovery elapsed time before a node is called accepted.
