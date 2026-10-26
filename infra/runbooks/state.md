# Independent state bootstrap and recovery

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.

## First bootstrap: no circular dependency

Use a separate German state project, admin keys, private control network and S3
backup owner/state/retention identities. This service must outlive all nodes.
It has no public DB endpoint. Bootstrap uses its default **local** backend:

1. On an encrypted EU workstation, disable swap/core dumps. Mount a private tmpfs,
   set `umask 077`, and copy the approved `infra/bootstrap` source there without
   `.terraform` or state. Keep provider credentials in private files/environment.
   Use a private example-derived tfvars file. Never use GitHub-hosted runners.
2. Run init/plan/review/apply locally in that tmpfs. Set `TF_DATA_DIR` inside it.
   After every operation, SOPS-encrypt `terraform.tfstate` with
   `infra/scripts/checkpoint.sh` to two independent EU destinations. Verify both
   copies decrypt and match serial/lineage. Encrypt plan/stdout/stderr too.
3. If interrupted before a checkpoint, query independent cloud inventory; import
   named VM/volume/network/keys/firewall/bucket/policy resources into the last
   recovered state. Compare IDs and attachments before any plan. Never recreate
   an existing disk, and never use `-force-copy` to hide a lineage conflict.
4. Verify the VM SSH host fingerprint out of band. Install the approved clean
   source through `infra/scripts/install-host.sh` and keep a copy of the exact
   approved code/image versions in the offline recovery record.

Prepare a **SOPS encrypted** state JSON bundle privately. Its fields are
`identity` (the complete Terraform operator_manifest object, including device,
hostname, admin CIDRs and approved German backup location/bucket),
`source_commit`, `db_password`, `tls_key`, `tls_cert`, `tls_ca`, `pgbackrest_conf`
and `monitor_curl` (private HTTPS EU heartbeat curl configuration).
`device` is the Terraform state_device output; hostname is the operator-CA
certificate SAN, for example `state.example.org`. Use an independently generated
CA, a server certificate/key and a strong PostgreSQL admin password.
The backup configuration uses `[state]`, PG16's data/socket paths from the managed
example, `/state/epoch-1`, the bootstrap bucket in the **other** German location,
state's restricted S3 key and independently escrowed AES passphrase.
Keep TLS verification, synchronous archive, expiry disabled, time-based 35-day
full retention and retained boundary WAL. No secret goes through Terraform.

Stream the decrypted JSON over verified SSH to
`python3 /usr/local/lib/bato/bootstrap/state.py configure --source /approved/source`.
Stop the state service before replacing its mounted secrets during rotation.
Configure writes mode-0400 UID999 files and a password-free Compose definition.
The state PG image is built from pinned PG16/pgvector/pgBackRest and the approved SHA.

Generate a random binary LUKS key in the EU encrypted custody store. Stream it
through verified SSH stdin to `state.py first-disk` **once, on a blank disk**.
This creates LUKS2/ext4, mounts `/dev/mapper/bato-state` at `/srv/bato-state`, and
writes a disk identity. No key appears in an argument or crypttab. Back up the
LUKS header into two encrypted EU stores. Database/WAL/temp live under PGDATA on
that mount; no unencrypted tablespaces/swap/core dumps are allowed.
Enable/start `bato-state-firewall.service`. Run `state.py initialize`, then
enable/start `bato-state.service`, `bato-state-backup.timer` and
`bato-state-monitor.timer`. On every reboot, operator stdin unlock through
`state.py unlock` precedes systemd start. No Docker restart policy bypasses this.

Create each database with a distinct name such as `example_dev`. Send a SOPS
decrypted JSON object containing `database` and independent `password` to
`state.py database`. The role is non-superuser/no-create-role/no-create-db,
owns only its database, and PUBLIC cannot connect. Repeat for prod.
The routine reads a temporary private file inside PostgreSQL rather than writing
password literals into SQL logs. If interrupted after role creation, reconcile
roles/databases manually before retrying; it never drops an existing database.
Use minimum permissions for plan-only logins: CONNECT, schema USAGE, state table
SELECT, sequence USAGE and PostgreSQL advisory locking; pre-create schemas/tables
with an operator init. Do not grant CREATE or state UPDATE to a CI plan login.

## Verified connectivity

Open `ssh -o StrictHostKeyChecking=yes -N -L 15432:127.0.0.1:5432 "$VERIFIED_STATE"`.
Use a password-free libpq URL such as:

```sh
export PG_CONN_STR="postgres://example_dev@state.example.org:15432/example_dev?sslmode=verify-full&sslrootcert=/private/state-ca.crt"
export PGPASSFILE=/private/backend.pgpass
export PG_SCHEMA_NAME=example_dev_node
terraform -chdir=infra/node init -input=false
```

The passfile matches the verified **hostname** and tunnel port. It is mode 0400.
Map `state.example.org` to `127.0.0.1` in the EU workstation/ephemeral runner's
private hosts resolver while using this tunnel. Terraform's lib/pq driver does
not support libpq's separate `hostaddr` parameter; keep the certificate hostname
as the connection host so verify-full checks its SAN. Restore the resolver entry
after closing the tunnel. Pre-created read-only plan schemas require
`PG_SKIP_SCHEMA_CREATION=true`, `PG_SKIP_TABLE_CREATION=true` and
`PG_SKIP_INDEX_CREATION=true`; the trusted wrapper sets all three.
The SSH host key and TLS SAN/CA must both verify; never use `sslmode=require`,
`accept-new`, `StrictHostKeyChecking=no` or a public 5432 rule. The host firewall
permits SSH only from the operator CIDRs and ICMP/NDP/replies; default-deny all
other inbound traffic for both families. Install this policy before accepting
the backend; do not reuse a node firewall with tenant HTTPS access.
Nodes have no control-network attachment/backend role.

In a **dedicated EU lab database**, run `infra/scripts/backend-acceptance.sh` with
`BATO_DEDICATED_LAB_DATABASE=yes`, `BATO_EU_TMPFS`, CA/passfile and TLS connection.
It exercises real Terraform native lock exclusion/release and encrypted-in-transit
state pull/push serial/lineage checks, and rejects a missing CA. Raw evidence stays
in EU tmpfs. It does not claim a physical cold restore.

## Monitoring, export and cold recovery

The installed five-minute state timer commits an operator-only heartbeat, checks
`pg_stat_archiver` failure/lag >15m, pgBackRest access/backup age >26h, encrypted
filesystem use >80%, TLS verification and expiry <21d. It sends success only if
every check passes. The existing EU monitor must independently probe service
reachability and alert after ten minutes without success. Deliver missing-
heartbeat/service/storage alerts within 15m through EU Alertmanager/mail.
Confirm initial alert delivery by blocking backup connectivity and stopping
the service in the lab. Export/encrypt every changed Terraform root state with
`terraform state pull` into tmpfs and checkpoint to two independent EU locations.

For backend loss, freeze changes; running nodes keep serving. Recover CA, TLS
key/cert, LUKS header/key, age identities, offline backup cipher key, bucket
inventory and bootstrap checkpoint from **independent** EU custodians.
Recreate/import the independent service with the local bootstrap checkpoint;
unlock the surviving disk or restore its physical pgBackRest full/WAL chain
onto **new** LUKS storage with the matching PG/pgBackRest versions.
Use `pgbackrest --stanza=state --pg1-path=/replacement/pgdata --type=time
--target="$RECOVERY_TIMESTAMP" --target-action=promote restore` in an isolated
recovery container with the retained repository/keys. Start with loopback/TLS
only. Verify databases/logins, latest committed markers, state serial/lineage
against encrypted exports and cloud inventory. Reject any unexplained mismatch
before planning. Repeat native lock and wrong-CA checks on the restored backend,
then repoint verified tunnels. Include this time in the four-hour recovery target.

Rotate CA/TLS/login/LUKS keys with overlap; verify both current access and old
checkpoint restoration before retiring keys. Keep old LUKS headers and repository
epoch keys for their entire retention period. Test interrupted bootstrap and
cold-key recovery initially and quarterly; record evidence outside GitHub.
