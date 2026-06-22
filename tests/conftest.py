"""Shared test fixtures.

During the Graphene → Strawberry migration the `client` fixture is **parametrized
over both schemas**, so every existing schema test runs against the legacy Graphene
schema *and* the new Strawberry schema. This enforces behavioural parity with the
test suite we already trust. At cutover, drop the `"legacy"` param (and the legacy
imports) and the same tests keep guarding the Strawberry schema.
"""

import pytest
from graphene.test import Client as GrapheneClient

from nshm_model_graphql_api import schema as legacy_schema
from nshm_model_graphql_api.strawberry_schema import schema as strawberry_schema


class StrawberryClient:
    """Adapter giving the Strawberry schema the `graphene.test.Client.execute()` shape.

    Returns a dict with `data` (and `errors` only when present), matching how the
    existing tests read results (`executed["data"]`, `executed["errors"]`).
    """

    def __init__(self, schema):
        self._schema = schema

    def execute(self, query, variables=None, **kwargs):
        result = self._schema.execute_sync(query, variable_values=variables)
        out = {"data": result.data}
        if result.errors:
            out["errors"] = [{"message": err.message} for err in result.errors]
        return out


@pytest.fixture(scope="module", params=["legacy", "strawberry"])
def client(request):
    """A GraphQL client over the legacy (Graphene) or new (Strawberry) schema."""
    if request.param == "legacy":
        return GrapheneClient(legacy_schema.schema_root)
    return StrawberryClient(strawberry_schema)
