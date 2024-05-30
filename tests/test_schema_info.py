import pytest
from graphene.test import Client

from nshm_model_graphql_api import __version__, schema


@pytest.fixture(scope="module")
def client():
    return Client(schema.schema_root)


def test_get_about(client):
    QUERY = """
    query {
        about
    }
    """
    executed = client.execute(QUERY)
    print(executed)
    assert "nshm_model_graphql_api" in executed["data"]["about"]
    assert __version__ in executed["data"]["about"]


def test_get_version(client):
    QUERY = """
    query {
        version
    }
    """
    executed = client.execute(QUERY)
    print(executed)
    assert __version__ in executed["data"]["version"]
