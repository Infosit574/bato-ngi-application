# Licensing and third-party dependencies

Copyright (C) 2026 Infosit d.o.o., the implementer of BATO.
This documentation is CC BY-SA 4.0.

## Scope

- BATO software, tests, build/deployment configuration, and automation are
  **AGPL-3.0-or-later**, under the unchanged grant in `license.txt`. The complete
  AGPL v3 text is in `LICENSES/AGPL-3.0-or-later.txt`; the filename does not alter
  the grant's option to use later versions.
- README, `docs/` and `infra/runbooks/` documentation are **CC BY-SA 4.0**; the complete text is in
  `LICENSES/CC-BY-SA-4.0.txt`. Original Infosit attribution and historical
  application/AI-assistance notices are retained.
- Third-party software and license texts keep their own licenses. They are not
  relicensed as BATO software or documentation. LGPL v3 and its incorporated GPL
  v3 text are included for the PostgreSQL driver. No model weights, datasets,
  proprietary service code, or noncommercial/source-available components are added
  to application images.

## Review and reproduction

The initial dependency review inspected PyPI metadata for every package/version
in `uv.lock`, including conditional Windows/timezone dependencies, and inspected
the installed license files with `pip-licenses`. Runtime dependencies resolve
only to MIT/MIT-0, BSD, Apache-2.0, PSF-2.0, MPL-2.0, and LGPL-3.0-only terms.
These are compatible with the AGPL v3 application when their attribution,
source-availability, and relinking obligations are respected. No dependency is
treated as compatible merely because it calls itself open source.

```sh
uv sync --locked
uv tree --locked --no-dev
uv run pip-licenses --with-system --with-urls --with-license-file
```

The lockfile contains exact versions, artifact URLs, and hashes. Resolve source
packages from each package's versioned PyPI page (`https://pypi.org/project/NAME/VERSION/`)
and upstream project links there. Do not strip installed `.dist-info` license
files or native-library notices when redistributing images or wheels.
The Docker runtime copies the complete environment, including those notices.
The source repository, lockfile, and build recipe must accompany any distribution
offer under the applicable source-disclosure terms; this skeleton does not
publish binary releases or claim a completed distribution-compliance service.

## Runtime dependency inventory

Versions below match the initial lock; refresh this review when updating it.

| Packages (version) | License |
| --- | --- |
| fastapi 0.161.0; mcp 1.30.0; pydantic 2.14.1 | MIT |
| psycopg 3.3.6; psycopg-binary 3.3.6 | LGPL-3.0-only |
| uvicorn 0.54.0; starlette 1.9.0; sse-starlette 3.5.0 | BSD-3-Clause |
| annotated-doc 0.0.5; annotated-types 0.8.0; anyio 4.15.1; attrs 26.1.0 | MIT |
| h11 0.16.0; httpx-sse 0.4.3; jsonschema 4.26.0; jsonschema-specifications 2025.9.1 | MIT |
| pydantic-core 2.50.1; pydantic-settings 2.16.1; PyJWT 2.15.1 | MIT |
| referencing 0.37.0; rpds-py 2026.9.1; typing-inspection 0.4.4 | MIT |
| click 8.5.0; httpcore 1.0.9; httpx 0.28.1; idna 3.20; pycparser 3.12; python-dotenv 1.2.4 | BSD-3-Clause |
| cryptography 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| cffi 2.1.1 | MIT-0 |
| opentelemetry-api 1.45.1; python-multipart 0.0.32 | Apache-2.0 |
| certifi 2026.10.19 | MPL-2.0 |
| typing-extensions 4.16.0; pywin32 312 (Windows only) | PSF-2.0 / PSF terms |
| tzdata 2026.5 (conditional) | Apache-2.0; underlying timezone data public domain |

The binary Psycopg distribution bundles native libraries. Psycopg is LGPL v3;
libpq uses the PostgreSQL License, and its bundled supporting libraries retain
their upstream terms. See [Psycopg binary distribution](https://www.psycopg.org/psycopg3/docs/basic/install.html#binary-installation)
and [source/build recipes](https://github.com/psycopg/psycopg).
Use compatible replacement shared libraries or rebuild from corresponding source
when modifying the driver; do not impose restrictions on relinking/debugging.
MPL components remain separate and unmodified; preserve their source and notices.

## Development/build dependencies

Development dependencies are not installed in the runtime image:

| Packages (version) | License |
| --- | --- |
| pytest 9.1.1; mypy 2.4.0; ruff 0.17.2; pip-licenses 5.5.5 | MIT |
| ast-serialize 0.13.1; iniconfig 2.3.1; librt 0.16.0; mypy-extensions 1.1.0; pluggy 1.7.0; wcwidth 0.9.3 | MIT |
| prettytable 3.18.0; colorama 0.4.6 (Windows only) | BSD-3-Clause |
| Pygments 2.21.0 | BSD-2-Clause |
| packaging 26.3 | Apache-2.0 OR BSD-2-Clause |
| pathspec 1.1.1 | MPL-2.0 |
| hatchling 1.30.1 (isolated build backend) | MIT |

Hatchling also uses the permissively licensed `trove-classifiers` build helper.
The build backend itself is pinned in `pyproject.toml`; isolated build helpers
are resolved by the build frontend, not by the runtime lock. Refresh their review
with backend updates. uv 0.11.4 uses MIT OR Apache-2.0. GitHub Actions checkout and
setup-uv are MIT-licensed build automation, not application runtime dependencies.

## Container licenses

Digest pins in `Dockerfile` and `compose.yaml` identify the reviewed image
artifacts; they are independent aggregates, not blanket AGPL relicensing:

- `python:3.12.15-slim-bookworm`: Python PSF license and the
  [official image recipe](https://github.com/docker-library/python) (MIT);
  Debian components retain their individual free-software licenses.
- `pgvector/pgvector:0.8.2-pg16-bookworm`: PostgreSQL 16 and pgvector use the
  [PostgreSQL License](https://github.com/pgvector/pgvector/blob/v0.8.2/LICENSE);
  the underlying PostgreSQL image and Debian packages retain their own notices.
- `ghcr.io/astral-sh/uv:0.11.4`: [uv](https://github.com/astral-sh/uv/tree/0.11.4)
  is MIT OR Apache-2.0 and is used only in the build stage.

Retain `/usr/share/doc/*/copyright`, Python's license files, and package notices.
Debian GPL/LGPL programs in these images remain independent system components.
Recheck package licenses and source obligations when changing the pinned images;
this inventory is not a vulnerability audit or a license for external services.

## Managed infrastructure tools

Managed deployment recipes retain the BATO AGPL-3.0-or-later grant; upstream
tools remain separate, unmodified aggregates under their own terms:

- Traefik 3.7.16 and bundled lego 5.5.2: MIT.
- pgBackRest 2.60.0: MIT; preserve its packaged notices and dependencies.
- SOPS: MPL-2.0; age: BSD-3-Clause; OpenSSH: its upstream BSD-style notices.
- Terraform 1.13.5: BUSL-1.1, a source-available operator tool, **not an
  open-source BATO dependency or relicensed AGPL software**.
- Terraform hcloud 1.70.2 and AWS 6.70.0 providers: MPL-2.0.

Retain image/package notices, source links and upstream licence obligations when
redistributing tools. No Terraform binary/provider is shipped in the BATO API
image. Its use does not change the application's or this repository's grants.
