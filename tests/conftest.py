"""Shared test fixtures.

The `client` fixture runs the schema tests against the Strawberry schema via a
small adapter that mimics `graphene.test.Client.execute()` (returns a `{data,
errors}` dict), so the original test bodies keep working unchanged.
"""

import pytest

from nshm_model_graphql_api.schema import schema as strawberry_schema


class StrawberryClient:
    """Adapter giving the Strawberry schema the `graphene.test.Client.execute()` shape.

    Returns a dict with `data` (and `errors` only when present), matching how the
    tests read results (`executed["data"]`, `executed["errors"]`).
    """

    def __init__(self, schema):
        self._schema = schema

    def execute(self, query, variables=None, **kwargs):
        result = self._schema.execute_sync(query, variable_values=variables)
        out = {"data": result.data}
        if result.errors:
            out["errors"] = [{"message": err.message} for err in result.errors]
        return out


@pytest.fixture(scope="module")
def client():
    """A GraphQL client over the Strawberry schema."""
    return StrawberryClient(strawberry_schema)
