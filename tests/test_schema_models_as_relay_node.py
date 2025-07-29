import pytest
from graphene.test import Client
from graphql_relay import to_global_id

from nshm_model_graphql_api import schema


@pytest.fixture(scope="module")
def client():
    return Client(schema.schema_root)


@pytest.mark.parametrize(
    "version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_as_node(client, version):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on NshmModel {
                version
                title
            }
        }
    }
    """ % to_global_id(
        "NshmModel", version
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["version"] == version
    assert executed["data"]["node"]["title"] is not None
    assert executed["data"]["node"]["id"] == to_global_id("NshmModel", version)
