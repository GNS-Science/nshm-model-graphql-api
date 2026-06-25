
# nshm-model-graphql-api

A GraphQL API for the `nzshm-model` library.

Built with Strawberry + FastAPI, deployed as an AWS Lambda (zip) via Serverless Framework v4 (Mangum ASGI adapter).

The GraphiQL interface is served from `/graphql` (GET); queries are POSTed to the same path.

## Getting started

```
uv sync --all-groups
yarn install
```

## Some useful commands

```
# local dev server (FastAPI) on http://localhost:8000/graphql
uv run --with uvicorn uvicorn nshm_model_graphql_api.app:app --reload

# tests / lint / types
uv run pytest
uv run ruff check nshm_model_graphql_api tests
uv run mypy nshm_model_graphql_api tests

# SDL parity check vs the committed baseline
uv run python -m nshm_model_graphql_api.tools.schema_parity
```
