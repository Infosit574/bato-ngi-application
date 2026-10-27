#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set -euo pipefail
test "$(id -u)" -eq 0
source_dir=$(realpath "${1:?clean approved source checkout required}")
approved=${2:?approved full source SHA required}
[[ "$approved" =~ ^[a-f0-9]{40}$ ]]
test "$(git -C "$source_dir" rev-parse HEAD)" = "$approved"
test -z "$(git -C "$source_dir" status --porcelain)"
test "$(uname -m)" = x86_64
. /etc/os-release
test "$ID" = debian
test "$VERSION_ID" = 12
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg nftables cryptsetup python3 git jq
install -m 0755 -d /etc/apt/keyrings
curl --fail --silent --show-error https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
fingerprint=$(gpg --show-keys --with-colons /etc/apt/keyrings/docker.asc)
[[ "$fingerprint" == *9DC858229FC7DD38854AE2D88D81803C0EBFCD88* ]]
printf '%s\n' 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable' > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
swapoff -a
sed -i '/[[:space:]]swap[[:space:]]/s/^/# disabled for managed state: /' /etc/fstab
install -d /etc/systemd/coredump.conf.d /etc/security/limits.d /usr/local/lib/bato/scripts /usr/local/lib/bato/bootstrap
printf '[Coredump]\nStorage=none\nProcessSizeMax=0\n' > /etc/systemd/coredump.conf.d/bato.conf
printf '* hard core 0\n* soft core 0\n' > /etc/security/limits.d/bato.conf
install -m 0644 "$source_dir/infra/scripts/node.py" /usr/local/lib/bato/scripts/node.py
install -m 0644 "$source_dir/infra/scripts/node.py" /usr/local/lib/bato/node.py
install -m 0644 "$source_dir/infra/bootstrap/state.py" /usr/local/lib/bato/bootstrap/state.py
install -m 0644 "$source_dir"/deploy/managed/*.service "$source_dir"/deploy/managed/*.timer /etc/systemd/system/
install -m 0644 "$source_dir"/infra/bootstrap/*.service "$source_dir"/infra/bootstrap/*.timer /etc/systemd/system/
install -d -m 0700 /var/lib/bato/acme
systemctl daemon-reload
