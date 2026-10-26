#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set -euo pipefail
set +x
umask 077
test "${BATO_DEDICATED_LAB_DATABASE:-}" = yes
[[ "${PG_CONN_STR:?}" == *sslmode=verify-full* ]]
test -n "${PGPASSFILE:?}"
test "$(findmnt -n -o FSTYPE "${BATO_EU_TMPFS:?}")" = tmpfs
work=$(mktemp -d "$BATO_EU_TMPFS/backend-check.XXXXXXXX")
PG_SCHEMA_NAME="acceptance_$(date -u +%s)"
export PG_SCHEMA_NAME
printf 'terraform { backend "pg" {} }\nresource "terraform_data" "lock" {\n provisioner "local-exec" { command = "sleep 8" }\n}\n' > "$work/main.tf"
terraform -chdir="$work" init -input=false > "$work/init.log" 2>&1
terraform -chdir="$work" apply -auto-approve -input=false > "$work/first.log" 2>&1 &
first=$!
sleep 3
if terraform -chdir="$work" apply -auto-approve -input=false -lock-timeout=1s \
    > "$work/concurrent.log" 2>&1; then
    printf 'FAIL: concurrent backend operation was not excluded\n' >&2
    exit 1
fi
wait "$first"
terraform -chdir="$work" plan -input=false -lock-timeout=1s > "$work/released.log" 2>&1
terraform -chdir="$work" state pull > "$work/before.json"
terraform -chdir="$work" state push "$work/before.json" > "$work/push.log" 2>&1
terraform -chdir="$work" state pull > "$work/after.json"
python3 - "$work" <<'PY'
import json
import pathlib
import sys
p = pathlib.Path(sys.argv[1])
a, b = [json.loads((p / name).read_text()) for name in ("before.json", "after.json")]
assert a["lineage"] == b["lineage"] and a["serial"] == b["serial"]
assert a["resources"] == b["resources"]
PY
if PG_CONN_STR="${PG_CONN_STR}&sslrootcert=$work/missing-ca.crt" \
    terraform -chdir="$work" state pull > "$work/invalid-tls.log" 2>&1; then
    printf 'FAIL: invalid CA was accepted\n' >&2
    exit 1
fi
printf 'PASS: native exclusion/release, state round trip and invalid-CA refusal; cold restore remains separate\n'
