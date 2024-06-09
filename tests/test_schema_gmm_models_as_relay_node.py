import pytest
from graphene.test import Client
from graphql_relay import to_global_id

from nshm_model_graphql_api import schema


@pytest.fixture(scope="module")
def client():
    return Client(schema.schema_root)


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_SourceLogicTree_as_node(client, model_version):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on GroundMotionModelLogicTree {
                model_version
            }
        }
    }
    """ % to_global_id(
        "GroundMotionModelLogicTree", model_version
    )
    print(QUERY)
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["id"] == to_global_id(
        "GroundMotionModelLogicTree", model_version
    )


@pytest.mark.parametrize(
    "model_version, short_name, long_name",
    [
        ("NSHM_v1.0.0", "CRU", "Crustal"),
        ("NSHM_v1.0.0", "SLAB", "Subduction Intraslab"),
        ("NSHM_v1.0.4", "CRU", "Crustal"),
        ("NSHM_v1.0.4", "INTER", "Subduction Interface"),
    ],
)
def test_get_model_GmmBranchSet_as_node(client, model_version, short_name, long_name):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on GmmBranchSet {
                model_version
                short_name
                long_name
                tectonic_region_type
            }

        }
    }
    """ % to_global_id(
        "GmmBranchSet", f"{model_version}:{short_name}"
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["short_name"] == short_name
    assert executed["data"]["node"]["long_name"] == long_name
    assert executed["data"]["node"]["id"] == to_global_id(
        "GmmBranchSet", f"{model_version}:{short_name}"
    )


@pytest.mark.parametrize(
    "model_version, branch_set_short_name, gsim_name, gsim_args, weight",
    [
        (
            "NSHM_v1.0.0",
            "CRU",
            "Stafford2022",
            '{"mu_branch": "Upper"}',
            0.117,
        ),
        (
            "NSHM_v1.0.4",
            "INTER",
            "Atkinson2022SInter",
            '{"epistemic": "Lower", "modified_sigma": "true"}',
            0.081,
        ),
    ],
)
def test_get_model_GmmLogicTreeBranch_as_node(
    client, model_version, branch_set_short_name, gsim_name, gsim_args, weight
):
    QUERY = """
    query {
        node(id: "%s")
        {
            ... on Node {
                id
            }
            ... on GmmLogicTreeBranch {
                model_version
                branch_set_short_name
                gsim_name
                gsim_args
                weight
            }

        }
    }
    """ % to_global_id(
        "GmmLogicTreeBranch",
        f"{model_version}|{branch_set_short_name}|{gsim_name}|{gsim_args}",
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["id"] == to_global_id(
        "GmmLogicTreeBranch",
        f"{model_version}|{branch_set_short_name}|{gsim_name}|{gsim_args}",
    )

    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["branch_set_short_name"] == branch_set_short_name
    assert executed["data"]["node"]["gsim_name"] == gsim_name
    assert executed["data"]["node"]["weight"] == weight
