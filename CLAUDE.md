# CLAUDE.md

## Project Overview

A GraphQL API exposing New Zealand Seismic Hazard Model (NSHM) data via AWS Lambda. Built with Python / Strawberry / FastAPI, deployed as a zip Lambda using Serverless Framework v4 (Mangum ASGI adapter).

## Common Commands

```bash
# Install dependencies
yarn install
uv sync --all-groups

# Run tests
uv run pytest
uv run pytest tests/test_schema_models.py          # single test file
uv run pytest tests/test_schema_models.py::test_fn  # single test function
uv run pytest --cov                                 # with coverage

# Lint & format
uv run ruff format nshm_model_graphql_api tests
uv run ruff check nshm_model_graphql_api tests
uv run mypy nshm_model_graphql_api tests

# Full CI suite via tox
tox                    # all environments: audit, py312, format, lint, build
tox -e py312           # tests only
tox -e lint            # lint only

# Local dev server (FastAPI on :8000)
uv run --with uvicorn uvicorn nshm_model_graphql_api.app:app --reload

# SDL parity check vs the committed baseline
uv run python -m nshm_model_graphql_api.tools.schema_parity

# Deploy
AWS_PROFILE=<profile> uv run yarn sls deploy --region ap-southeast-2 --stage dev
```

## Architecture

**Query-only GraphQL API** — no mutations. The API wraps the `nzshm-model` Python library, which contains the actual NSHM data.

### Schema (`nshm_model_graphql_api/`)

- `app.py` — FastAPI app + `strawberry.fastapi.GraphQLRouter` at `/graphql`; `handler = Mangum(app)` is the Lambda entry point.
- `schema.py` — the Strawberry schema: root `QueryRoot` (`get_models`, `get_model`, `current_model_version`, `about`, `version`, `node`) and the 7 types (`NshmModel`; `SourceLogicTree` → `SourceBranchSet` → `SourceLogicTreeBranch` + `BranchSource` union; `GroundMotionModelLogicTree` → `GmmBranchSet` → `GmmLogicTreeBranch`), `JSONString` scalar, and a **custom `Node` interface** (keeps `id: ID!` + `graphql_relay` global-id encoding rather than Strawberry's `GlobalID`).
- `data.py` — graphene-free data-access layer over the `nzshm-model` dataclasses (cached getters). Resolvers project these into the GraphQL types.

`Schema(config=StrawberryConfig(auto_camel_case=False))` — field names are snake_case (the established client contract). SDL parity with the original Graphene schema is pinned by `schema.legacy.graphql` + `tests/test_schema_parity.py`.

### Deployment

Serverless Framework v4 deploys a zip Lambda (Python 3.12, 1024 MB, 10s timeout) in `ap-southeast-2`. API Gateway provides HTTP endpoints with API-key auth on POST. Python deps are packaged by SF v4's **built-in** python-requirements (activated by `custom.pythonRequirements`); the `deploy` npm script generates `requirements.txt` from uv first.

- `serverless.yml` — Lambda function (`handler: nshm_model_graphql_api.app.handler`), API Gateway routes, `custom.pythonRequirements`.
- `package.json` — Serverless CLI + plugins.

## Tech Stack

- **Runtime**: Python 3.12, Node 22 (for the Serverless CLI)
- **GraphQL/web**: Strawberry, FastAPI, Mangum
- **Package managers**: uv (Python), Yarn v4 (Node)
- **Testing**: pytest (Strawberry schema; SDL-parity + live corpus-replay checks)
- **CI/CD**: GitHub Actions (`.github/workflows/`) — tests on PR, deploy on push to `deploy-test`/`main`
- **Version management**: bump2version syncs version across `pyproject.toml`, `package.json`, `__init__.py` — **also run `uv lock` after a bump** (bump2version doesn't update the lockfile)

## Configuration

- `pyproject.toml` — uv dependencies, project metadata, ruff, mypy config
- `setup.cfg` — pytest, coverage, tox settings
- `.bumpversion.cfg` — version bump targets
- `docs/MIGRATION_LOG.md`, `docs/PHASE5_CUTOVER.md` — the Graphene→Strawberry migration record + cutover/rollback runbook
