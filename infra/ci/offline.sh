#!/bin/bash
# Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later.
set -euo pipefail
terraform fmt -check -recursive infra
for root in bootstrap retained node; do
    terraform -chdir="infra/$root" init -backend=false -input=false -lockfile=readonly
    terraform -chdir="infra/$root" validate
    for environment in dev prod; do
        terraform -chdir="infra/$root" test -var-file="examples/$environment.tfvars"
    done
done
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/test_infrastructure.py
for script in infra/scripts/*.sh infra/ci/*.sh; do
    bash -n "$script"
    docker run --rm -i koalaman/shellcheck:v0.11.0@sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d \
        --severity=warning -s bash - < "$script"
done
for workflow in .github/workflows/*.yml; do
    docker run --rm -i \
        --mount "type=bind,src=$PWD/.github/actionlint.yaml,dst=/actionlint.yaml,readonly" \
        rhysd/actionlint:1.7.7@sha256:887a259a5a534f3c4f36cb02dca341673c6089431057242cdc931e9f133147e9 \
        -config-file /actionlint.yaml -shellcheck= - < "$workflow"
done
BATO_SOURCE_COMMIT=1111111111111111111111111111111111111111 \
    docker compose -f compose.yaml -f deploy/managed/compose.yaml config --quiet
