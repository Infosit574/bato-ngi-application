# Trusted exact-SHA plan runner

Copyright (C) 2026 Infosit d.o.o. Documentation: CC BY-SA 4.0.

All PRs run public offline checks with no credentials. Real plans cannot run
without cloud/backend credentials and private identifiers. No apply job exists.

## Required controls before enabling manual plans

Provisioning a runner is **operator work with separate spending approval**, not
part of PR CI. Use a single-job ephemeral German runner on an isolated control
network, never on a node/state host. Restrict its GitHub runner group to this
workflow at protected refs only; a label alone is **not** a security boundary.
Do not register it as a general public-repository runner. Deny arbitrary PR/fork
workflows, remove other runner groups with matching access, and require approvals
on `managed-plan-dev`/`managed-plan-prod` environments. Approvers must inspect the
full source SHA and the workflow ref, not only a PR number.
Workflow dispatch must select the same protected ref as `reviewed_sha`.
Before merging to a protected ref, plans remain operator-local.

Install `infra/ci/trusted-plan.sh` as the root-owned, non-runner-writable
`/usr/local/sbin/bato-approved-plan`. The job executes no checkout or repository
shell script. Preinstall checksum-verified Terraform 1.13.5 and age.
Preclone the public repository to `/var/lib/bato-plan/repository` without forge
credentials. Root owns `/etc/bato-plan` and its subdirectories (0750), and their
configuration/approval files (0640), with a dedicated runner group. The service
account joins that group for read-only access; it cannot replace approval files.
The configuration includes:

- `residency`: the literal `Germany`, created only after checking provider VM
  location/network/inventory. This is an operator attestation, not geolocation.
- `approved/FULL_SHA`: a file the operator creates **after** reviewing the exact
  SHA; do not automatically create it from job input.
- `recipients.txt`: offline age recipients, no private decryption identities.
- `dev/provider-backend.env` and prod equivalent: private exported provider
  read-only token, independent S3 planning credential, password-free TLS
  `PG_CONN_STR`, mode-0400 `PGPASSFILE` and `BATO_TENANT`.
- `dev/node.tfvars`, `dev/retained.tfvars` and prod equivalents: public-resource
  inputs privately scoped to that tenant/project/database, with no node bundles.

Keep `PGPASSFILE` owned by the service account at mode 0400 in the root-owned
environment directory. It is the exception to the root-owned 0640 file rule.

The runner needs read APIs for resource refresh. The backend plan role has only
existing schema/state reads and advisory lock access. Bootstrap schemas and tables
operator-side first; do not permit CI init to create databases or change state.
The hcloud provider needs the selected project token; credentials from another
tenant/project must not be available to the job.

Set the retained root's `plan_principal` to that planning key's public ARN.
Use a separate credentials project and a key distinct from node, retention and
offline owner keys. The bucket policy exempts it from the unnamed-key deny and
allows only the metadata reads used by AWS provider 6.70.0, including policy,
ACL, CORS, versioning, lifecycle and object-lock configuration refresh.
HeadBucket requires `ListBucket`, so the key can list this bucket's object names;
it cannot read object contents. Explicit denies block object reads, writes,
deletion and policy/ACL changes even if project defaults grant them.
No node, retention or owner credential belongs on the runner.

Mount private no-swap tmpfs at `/run/bato-plan` and EU encrypted storage at
`/mnt/bato-plan-eu` (0700). Verify destinations/backups stay in the approved EU
boundary. Disable GitHub step/runner debug, Terraform TF_LOG, shell tracing,
worker crash dumps and verbose diagnostics. Never upload/cache raw plans,
Terraform stdout/stderr/state or backend config with Actions artifacts.

## Run, record, and tear down

The wrapper rejects short SHAs, non-German attestation, wrong storage mounts,
missing approval, debug mode, password-bearing backend URLs and unsafe passfiles.
It locks a persistent monthly ledger under `/var/lib/bato-plan`, reserves a
30-minute slot, and refuses reservations beyond 36,000 seconds/month. The ledger
must live on the independent encrypted EU control store across ephemeral hosts;
resetting it each job defeats the budget. One lock allows only one job at once.
The workflow timeout is 30 minutes and Terraform plan has its own 25-minute limit.
The provisioning scheduler must tear down the VM after one job or 30 minutes,
including cancellation/offline loss, and refuse new runners at the quota. The
wrapper cannot enforce cloud VM billing/teardown by itself.

All raw init/plan/show/state output stays in tmpfs and an age-encrypted EU archive.
Failure triggers the same encrypted archive path. GitHub sees only command
exit/status and control-plane metadata. The operator reads raw errors privately;
do not paste them into GitHub. On cancellation/power loss, recover encrypted
tmpfs/host evidence according to custody policy or record the interrupted run;
never forward worker diagnostics with credentials to GitHub. Destroy the
single-job host after preserving the archive. Test deliberate failed init/plan
and cancellation to verify no raw output escapes.
