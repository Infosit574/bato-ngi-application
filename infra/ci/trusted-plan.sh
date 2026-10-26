#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set +x
set -euo pipefail
exec > /dev/null 2>&1
umask 077
sha=${1:?}
root=${2:?}
environment=${3:?}
[[ "$sha" =~ ^[a-f0-9]{40}$ ]]
[[ "$root" == node || "$root" == retained ]]
[[ "$environment" == dev || "$environment" == prod ]]
test "$(id -u)" -ne 0
test "${ACTIONS_STEP_DEBUG:-false}" != true
test "${ACTIONS_RUNNER_DEBUG:-false}" != true
test "$(stat -c '%u:%a' /etc/bato-plan)" = 0:750
test "$(stat -c '%u:%a' /etc/bato-plan/approved)" = 0:750
test "$(stat -c '%u:%a' "/etc/bato-plan/approved/$sha")" = 0:640
test -r "/etc/bato-plan/approved/$sha"
test "$(cat /etc/bato-plan/residency)" = Germany
exec 9>/var/lib/bato-plan/budget.lock
flock -n 9
month=$(date -u +%Y-%m)
ledger="/var/lib/bato-plan/$month.seconds"
used=$(cat "$ledger" 2>/dev/null || printf 0)
[[ "$used" =~ ^[0-9]+$ ]]
test "$((used + 1800))" -le 36000
printf '%s\n' "$((used + 1800))" > "$ledger"
test "$(findmnt -n -o FSTYPE /run/bato-plan)" = tmpfs
test "$(findmnt -n -o TARGET --target /mnt/bato-plan-eu)" = /mnt/bato-plan-eu
test "$(stat -c %a /mnt/bato-plan-eu)" = 700
test -f /etc/bato-plan/recipients.txt
work=$(mktemp -d /run/bato-plan/plan.XXXXXXXX)
finish() {
    result=$?
    trap - EXIT
    tar -C "$work" -czf - . | age -R /etc/bato-plan/recipients.txt \
        -o "/mnt/bato-plan-eu/$sha-$root-$environment-$(date -u +%s).tar.gz.age" || result=1
    exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
unset TF_LOG TF_LOG_PATH
export TF_IN_AUTOMATION=1 TF_INPUT=0 CHECKPOINT_DISABLE=1
# shellcheck source=/dev/null
. "/etc/bato-plan/$environment/provider-backend.env"
test -n "${PGPASSFILE:-}"
test "$(stat -c %a "$PGPASSFILE")" = 400
[[ "$PG_CONN_STR" == *sslmode=verify-full* ]]
[[ "$PG_CONN_STR" != *password* && "$PG_CONN_STR" != *://*:*@* ]]
export PG_SCHEMA_NAME="${BATO_TENANT:?}_${environment}_${root}"
export PG_SKIP_SCHEMA_CREATION=true PG_SKIP_TABLE_CREATION=true PG_SKIP_INDEX_CREATION=true
git -C /var/lib/bato-plan/repository fetch origin "$sha" > "$work/fetch.log" 2>&1
test "$(git -C /var/lib/bato-plan/repository rev-parse "$sha")" = "$sha"
git -C /var/lib/bato-plan/repository archive "$sha" infra | tar -x -C "$work"
terraform -chdir="$work/infra/$root" init -input=false -lockfile=readonly > "$work/init.log" 2>&1
timeout --signal=TERM --kill-after=30 1500 terraform -chdir="$work/infra/$root" plan \
    -input=false -lock-timeout=60s -var-file="/etc/bato-plan/$environment/$root.tfvars" \
    -out="$work/plan" > "$work/plan.log" 2>&1
terraform -chdir="$work/infra/$root" show -json "$work/plan" > "$work/plan.json" 2> "$work/show.log"
terraform -chdir="$work/infra/$root" state pull > "$work/state.json" 2> "$work/state.log"
