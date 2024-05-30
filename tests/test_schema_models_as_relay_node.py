import pytest
from graphene.test import Client

from nshm_model_graphql_api import schema

from graphql_relay import to_global_id


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

@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_source_logic_tree_as_node(client, model_version):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on SourceLogicTree {
                model_version
            }
        }
    }
    """ % to_global_id(
        "SourceLogicTree", model_version
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["id"] == to_global_id("SourceLogicTree", model_version)


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_branch_set_as_node(client, model_version, short_name="CRU"):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on SourceBranchSet {
                model_version
                short_name
            }

        }
    }
    """ % to_global_id(
        "SourceBranchSet", f'{model_version}:{short_name}'
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["short_name"] == short_name
    assert executed["data"]["node"]["id"] == to_global_id("SourceBranchSet", f'{model_version}:CRU')


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_source_logic_tree_branch_as_node(client, model_version, branch_set_short_name="PUY",
    tag="[dm0.7, bN[0.902, 4.6], C4.0, s0.28]"):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on SourceLogicTreeBranch {
                model_version
                branch_set_short_name
                tag
                weight
            }

        }
    }
    """ % to_global_id(
        "SourceLogicTreeBranch", f'{model_version}:{branch_set_short_name}:{tag}'
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["id"] == to_global_id("SourceLogicTreeBranch", f'{model_version}:{branch_set_short_name}:{tag}')

    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["branch_set_short_name"] == branch_set_short_name
    assert executed["data"]["node"]["tag"] == tag
    assert executed["data"]["node"]["weight"] == 0.21

