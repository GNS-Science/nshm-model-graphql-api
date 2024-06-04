import pytest
from graphene.test import Client

from nshm_model_graphql_api import schema


@pytest.fixture(scope="module")
def client():
    return Client(schema.schema_root)


def test_get_models(client):
    QUERY = """
    query {
        get_models {
            version
        }
    }
    """
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["get_models"][0]["version"] == "NSHM_v1.0.0"


def test_get_model_default(client):
    QUERY = """
        query {
            get_model
            {
                version
            }
        }
    """
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["get_model"]["version"] == "NSHM_v1.0.4"


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model(client, model_version):
    QUERY = (
        """
    query {
        get_model(version: "%s")
        {
            __typename
            version
            ... on Node {
                id
            }
        }
    }
    """
        % model_version
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["get_model"]["version"] == model_version
    assert executed["data"]["get_model"]["__typename"] == "NshmModel"
