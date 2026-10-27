#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set -euo pipefail
set +x
umask 077
state=${1:?local tmpfs state or exported state file}
output_a=${2:?first independent EU checkpoint path}
output_b=${3:?second independent EU checkpoint path}
test "$(findmnt -n -o FSTYPE --target "$state")" = tmpfs
test -n "${SOPS_AGE_RECIPIENTS:?}"
test "$output_a" != "$output_b"
sops encrypt --input-type json --output-type json "$state" > "$output_a.next"
mv "$output_a.next" "$output_a"
cp "$output_a" "$output_b.next"
mv "$output_b.next" "$output_b"
