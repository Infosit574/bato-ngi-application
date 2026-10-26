# Physical backups, PITR, decommission and named purge

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.

## Repository interoperability and retention

Hetzner S3 has no default at-rest encryption. pgBackRest's `aes-256-cbc`
client-side encryption is mandatory, independent of optional SSE-C. TLS verifies
the endpoint. Use `fsn1` backups for `nbg1` compute and vice versa.
Hetzner supports S3 bucket policies with `pPROJECT:ACCESSKEY` principals and
NotPrincipal; it does **not** support NotAction. References:
[supported actions](https://docs.hetzner.com/storage/object-storage/supported-actions/),
[per-key credentials/policies](https://docs.hetzner.com/storage/object-storage/faq/s3-credentials/).
Private buckets alone do not isolate keys within the same project.

Node keys belong to separate credentials projects, have only their repository
path, and cannot delete objects/change ACL/policy/lifecycle. Do not reuse node
keys across tenants/buckets. Keep the bucket owner and off-node retention
principals offline/on the existing EU maintenance host, never on nodes or in CI.
No automatic S3 age lifecycle is installed: object ages alone do not understand
full/differential/WAL dependencies. The bucket and disk have Terraform
prevent_destroy; the disk also has provider deletion protection. Protection is
not a replacement for separate state and credential custody.

After paid authorization, run `infra/scripts/check-object-storage.sh` against
a dedicated acceptance bucket/prefix with the real restricted node and retention
profiles. Confirm write/read, node delete denial, cross-tenant denial and off-node
delete. Also test denied GET/list outside the repository and denied bucket
policy/ACL changes. Then run actual pgBackRest stanza-create/check, full,
differential, synchronous archive-push and restore against Hetzner S3 with those
same policies. **Mocked Terraform and a POSIX backup cannot prove S3 compatibility.**
Preserve any interoperability failure; never loosen node deletion rights.

pgBackRest 2.60 runs weekly Sunday full/daily differential and synchronous
archive-push. PostgreSQL's `archive_timeout=300s` forces bounded WAL turnover;
never configure archive-push-queue-max (which can drop WAL). Auto-expiry is off.
The off-node retention host receives its **own** pgBackRest config, encryption
key and deletion-capable principal. Use the matching pinned image and:

```sh
pgbackrest --config=/private/retention.conf --stanza=bato info
pgbackrest --config=/private/retention.conf --stanza=bato expire
```

Both configs keep `repo1-retention-full-type=time`, `repo1-retention-full=35`,
and `repo1-retention-archive-type=full`. Expire preserves the full backup needed
at the time boundary and its dependent WAL; do not set an independent shorter
archive retention. Confirm an actual oldest-target restore >=30 days ago before
the first expiry and every quarter. Coordinate expiry with backup/restore:
pause the node backup timer and operator updates, acquire the maintenance lock
in the shared EU schedule, run one expiry, then resume. Never run concurrent
node backup and off-node metadata rewriting without coordination.
Disable expiry on decommission so a frozen recovery chain does not age out.

An interrupted pgBackRest backup can need deletion of partial backup files,
even with `resume=n`. The restricted node must fail closed in that case. On the
off-node host, inspect `info`/backup manifests, preserve completed chains, and
clean only the identified incomplete backup with the retention principal under
maintenance approval. Verify a new full and restore before resuming schedule.
Do not grant the node a delete exception or delete queued WAL.

## Restore and measured acceptance

1. Start a timestamped incident/drill record in encrypted EU storage. Record the
   latest committed operator heartbeat and application-free synthetic marker.
   Freeze writes, expiry, updates and DNS cutover. Recover the backend first
   if unavailable, following the independent state runbook.
2. Select a completed full/differential and WAL chain covering the target time.
   Recover its offline epoch cipher key and matching PG16/pgvector/pgBackRest
   versions. Provision separately approved **replacement** retained storage and
   isolated compute; keep the original disk/bucket untouched.
3. Mount the new identified disk, inject recovery secrets, stop every writer.
   Use a recovery-only container, no public ports, mounted backup config and
   replacement PGDATA. Run `pgbackrest --stanza=bato --pg1-path=/replacement/pgdata
   --type=time --target="$RECOVERY_TIMESTAMP" --target-action=promote restore`.
   Never use `--delta` against the live/original data directory.
4. Start the restored database privately. Check `pg_is_in_recovery() = false`,
   `PG_VERSION=16`, included/excluded synthetic markers, vector distance query,
   non-superuser API role and API readiness. The local automated test executes
   this sequence on disposable POSIX storage; repeat it on real S3/LUKS.
5. Reconcile restored state serial/lineage with inventory. Check encrypted
   repository bytes, wrong-key refusal and old-key recovery. Verify IPv4/IPv6
   allow/deny, closed 80/5432/8000 and a real DNS-01 renewal on an owned domain.
   Switch DNS only after HTTPS/readiness and EU alert delivery pass.
6. Record last recoverable committed marker loss <=1h and total recovery <4h,
   including operator response/backend/key recovery/HTTPS. These are targets,
   not claims until measured. Initially/quarterly include a 30-day boundary
   restore and simulated backend loss; local minute-long history is insufficient.

Scan synthetic secret canaries in Terraform state/plan, user_data, process
arguments, Compose config/inspect and logs. No canary may appear. Check missing
secrets/wrong or unmounted disks refuse initialization/start/restart. Verify
reboot/update keeps marker data, database rotation, revoked DNS/S3 keys and old
backup keys. Keep all raw evidence EU-encrypted, not public CI artifacts.

## Ordinary destroy and separate irreversible purge

Ordinary decommission: freeze writes; run/check a final full and marker restore;
stop node/backup/monitor timers; freeze off-node expiry. Destroy **only the node
root** using its exact tenant/environment backend and reviewed plan. This removes
DNS/compute/network/firewall/attachment but not retained disk/bucket/objects/keys.
Keep the state service, retained root, encrypted checkpoints and custody inventory.
Charges continue indefinitely until a separately approved purge.

Never `destroy` the retained/bootstrap root, disable protection, empty a bucket,
run `state rm`, or delete keys as part of ordinary destroy.
For irreversible purge, obtain separate written approval naming **exact** tenant,
environment, disk ID, bucket name, repository epochs, retention window and key IDs.
Require a second operator to verify the inventory and that no other environment
or shared state service uses them. Export/checkpoint the final states first.
In a dedicated reviewed purge change, remove prevent_destroy **only for the named
resources**, disable the named disk's provider protection, list all bucket object
versions/multipart uploads and review the deletion inventory. The off-node owner
deletes only those objects and bucket after retention obligations pass; then
operator-apply the named disk deletion. Reconcile state/import as necessary, record
provider deletion receipts and only then retire the corresponding cipher/LUKS
keys under two-person custody. Do not supply a reusable bulk-delete command or
change `force_destroy` globally. Bootstrap/state service purge is a separate event.
