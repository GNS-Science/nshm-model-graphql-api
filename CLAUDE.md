# CLAUDE.md

## Project Overview

A GraphQL API exposing New Zealand Seismic Hazard Model (NSHM) data via AWS Lambda. Built with Python/Flask/Graphene, deployed using Serverless Framework v4.

## Common Commands

```bash
# Install dependencies
yarn install
poetry install

# Run tests
poetry run pytest
poetry run pytest tests/test_schema_models.py          # single test file
poetry run pytest tests/test_schema_models.py::test_fn  # single test function
poetry run pytest --cov                                 # with coverage

# Lint & format
poetry run black nshm_model_graphql_api tests
poetry run isort nshm_model_graphql_api tests
poetry run flake8 nshm_model_graphql_api tests
poetry run mypy nshm_model_graphql_api tests

# Full CI suite via tox
tox                    # all environments: audit, py312, format, lint, build
tox -e py312           # tests only
tox -e lint            # lint only

# Local dev server (port 5000)
ENABLE_METRICS=0 poetry run yarn sls wsgi serve

# Deploy
AWS_PROFILE=<profile> poetry run yarn sls deploy --region ap-southeast-2 --stage dev
```

## Architecture

**Query-only GraphQL API** — no mutations. The API wraps the `nzshm-model` Python library, which contains the actual NSHM data.

### Schema Structure (`nshm_model_graphql_api/schema/`)

- `schema_root.py` — Root query type with top-level resolvers (`get_models`, `get_model`, `current_model_version`, `about`, `version`, `node`)
- `nshm_model_schema.py` — `NshmModel` type with nested `source_logic_tree` and `gmm_logic_tree`
- `nshm_model_sources_schema.py` — Source logic tree types: `SourceLogicTree` → `SourceBranchSet` → `SourceBranch` → `InversionSource`/`DistributedSource`
- `nshm_model_gmms_schema.py` — Ground motion model logic tree types: `GmmLogicTree` → `GmmBranchSet` → `GmmBranch`

All types implement Relay's `Node` interface for global ID-based lookups. Resolvers use `@functools.lru_cache` for expensive data fetches.

### Flask App

`nshm_model_graphql_api/nshm_model_graphql_api.py` — Flask app factory. Serves GraphQL at `/graphql` (POST for queries, GET for GraphiQL interface).

### Deployment

Serverless Framework v4 deploys to AWS Lambda (Python 3.12, 2048MB, 10s timeout) in `ap-southeast-2`. API Gateway provides HTTP endpoints with API key auth on POST.

- `serverless.yml` — Lambda functions, API Gateway routes, WSGI config
- `package.json` — Serverless CLI and plugins (serverless-wsgi, serverless-plugin-warmup)

## Tech Stack

- **Runtime**: Python 3.12, Node 22 (for Serverless CLI)
- **Package managers**: Poetry (Python), Yarn v4 (Node)
- **Testing**: pytest with Graphene test Client
- **CI/CD**: GitHub Actions (`.github/workflows/`) — tests on PR, deploy on merge to main
- **Version management**: bump2version syncs version across `pyproject.toml`, `package.json`, `__init__.py`

## Configuration

- `pyproject.toml` — Poetry dependencies and project metadata
- `setup.cfg` — pytest, coverage, flake8, mypy, tox, isort settings
- `.bumpversion.cfg` — version bump targets
