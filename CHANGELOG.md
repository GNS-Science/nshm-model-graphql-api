# Changelog


## [0.5.0] - 2026-06-24

Pilot of the four-sibling Graphene → Strawberry migration. Deployed to the test stage and validated (19/19 differential parity vs the live legacy test + prod stages); prod promote pending. See `docs/MIGRATION_LOG.md`.

### Changed
 - Migrated the GraphQL stack from Graphene 3 / Flask / serverless-wsgi to **Strawberry / FastAPI / Mangum**, preserving the schema at SDL + runtime parity (snake_case via `auto_camel_case=False`, custom `Node` interface for `id: ID!` parity, `BranchSource` union, `gsim_args` JSON scalar)
 - Lambda dependency packaging now via Serverless Framework v4 built-in python-requirements (dropped `serverless-wsgi`)
 - Function memory 2048 → 1024 MB
 - deps: patch (12 pkgs), minor (35 pkgs), major: cryptography 46→49, lxml 6.0→6.1, mypy 1→2 (msgpack 1.2.1 fix blocked by 1-week age cutoff); configured dependency age cutoff
 - README: replaced poetry commands with uv equivalents

### Added
 - SDL-parity + client-query-corpus replay test gates; differential live-validation driver (`tests/smoke/drive_live.py`)

### Removed
 - Legacy Graphene/Flask app, `schema/` package, and deps (`flask`, `flask-cors`, `graphene`, `graphql-server`)
 - `serverless-plugin-warmup` (unused)

## [0.4.2] - 2026-04-29

### Changed
 - migrated from poetry to uv
 - dependency upgrades

## [0.4.1] - 2026-03-18

### Changed
 - dependency upgrades; add upgrade skill
 - removed `serverless-python-requirements` plugin
 - serverless.yml: added organization + app configuration (Serverless Framework v4)
 - dev.yml: dropped scheduled run

## [0.4.0] - 2025-10-20

### Changed
 - migrate to serverless 4
 - use python 3.12
 - migrate pyproject.toml to PEP508
 - ensureCI/CD workflows use minimum install footprints
 - update to `nzshm-model 0.14.0`

### Added
 - tox audit step

## [0.3.1] - 2025-09-15

### Changed
 - graphql-server pinned
 - dev dependencies updated

## [0.3.0] - 2025-07-29

### Changed
 - flake8 config
 - new about and version resolvers

### Added
 - Node resolver support for NshmModel
 - get_model resolver
 - get_models resolver
 - source logic tree models and resolvers
 - gmmm logic tree models and resolvers

## [0.2.0] - 2024-06-07
### Changed
 - Complete reset, no more django
 - all previous code is mothballed

## [0.1.3] - 2023-09-04
### Added
 - new about and version resolvers

## [0.1.2] - 2023-09-04
### Changed
 - configure static_url correctly for both local & AWS

## [0.1.1] - 2023-09-01
### Added
 - pytest, tox, etc
 - bumpversion & CHANGELOG.md

## [0.1.0] - 2023-09-01
* First version.

