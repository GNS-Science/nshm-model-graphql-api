"""Strawberry GraphQL schema (migration target).

Phase 1 bootstrap: this currently exposes only the scalar root fields so the
FastAPI/Mangum scaffold can boot and be smoke-tested. Phase 2 ports the full
type tree (NshmModel, source/gmm logic trees, the BranchSource union) and the
Relay Node interface from the legacy Graphene schema in `schema/`.

`auto_camel_case=False` is mandatory — the legacy schema uses snake_case field
names and every existing client depends on them (runbook Trap #2).

Once the legacy `schema/` package is removed at cutover, this module can be
renamed to `schema.py` to match the runbook's target layout.
"""

import strawberry
from strawberry.schema.config import StrawberryConfig

from nshm_model_graphql_api import __version__

# Reused from the legacy schema for behavioural parity; will move into the
# Strawberry type tree in Phase 2.
from nshm_model_graphql_api.schema.nshm_model_schema import get_current_model_version


@strawberry.type
class Query:
    """This is the entry point for all graphql query operations."""

    # Return types are Optional to match the legacy Graphene SDL exactly
    # (graphene String is nullable). Don't tighten the contract mid-migration.
    @strawberry.field(description="About this API ")
    def about(self) -> str | None:
        return f"Hello, I am nshm_model_graphql_api, version: {__version__}!"

    @strawberry.field(description="API version string")
    def version(self) -> str | None:
        return __version__

    @strawberry.field
    def current_model_version(self) -> str | None:
        return get_current_model_version()


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(auto_camel_case=False),
)
