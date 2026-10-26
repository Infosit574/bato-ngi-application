#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set -euo pipefail
set +x
umask 077
bucket=${1:?dedicated acceptance bucket}
repo=${2:?tenant/environment/epoch-1}
endpoint=${3:?https://German endpoint}
node_profile=${4:?node profile}
retention_profile=${5:?off-node retention profile}
[[ "$endpoint" =~ ^https://(fsn1|nbg1)\.your-objectstorage\.com$ ]]
[[ "$repo" =~ ^[a-z0-9-]+/(dev|prod)/epoch-1$ ]]
work=$(mktemp -d "${BATO_EU_TMPFS:?}/s3-check.XXXXXXXX")
canary="$repo/acceptance-$(date -u +%s)"
printf 'synthetic backup policy canary\n' > "$work/canary"
aws --endpoint-url "$endpoint" --profile "$node_profile" s3api put-object \
    --bucket "$bucket" --key "$canary" --body "$work/canary" > "$work/put.json"
aws --endpoint-url "$endpoint" --profile "$node_profile" s3api get-object \
    --bucket "$bucket" --key "$canary" "$work/received" > "$work/get.json"
cmp "$work/canary" "$work/received"
if aws --endpoint-url "$endpoint" --profile "$node_profile" s3api delete-object \
    --bucket "$bucket" --key "$canary" > "$work/delete.json" 2> "$work/delete.error"; then
    printf 'FAIL: node could delete\n' >&2
    exit 1
fi
if aws --endpoint-url "$endpoint" --profile "$node_profile" s3api put-object \
    --bucket "$bucket" --key "other-tenant/prod/epoch-1/canary" --body "$work/canary" \
    > "$work/cross.json" 2> "$work/cross.error"; then
    printf 'FAIL: cross-tenant write allowed\n' >&2
    exit 1
fi
aws --endpoint-url "$endpoint" --profile "$retention_profile" s3api delete-object \
    --bucket "$bucket" --key "$canary" > "$work/retention.json"
printf 'PASS: write/read, node delete denial, cross-tenant denial and off-node removal\n'
