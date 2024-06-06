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
        ("NSHM_v1.0.0", "Active Shallow Crust", "Crustal"),
        # ("NSHM_v1.0.0", "PUY", "Puysegur"),
        # ("NSHM_v1.0.4", "CRU", "Crustal"),
        # ("NSHM_v1.0.4", "PUY", "Puysegur"),
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
    assert executed["data"]["node"]["tectonic_region_type"] == short_name
    # assert executed["data"]["node"]["long_name"] == long_name
    assert executed["data"]["node"]["id"] == to_global_id(
        "GmmBranchSet", f"{model_version}:{short_name}"
    )


'''

@pytest.mark.parametrize(
    "model_version, branch_set_short_name, tag, weight",
    [
        (
            "NSHM_v1.0.0",
            "CRU",
            "[dmgeologic, tdFalse, bN[1.089, 4.6], C4.2, s1.0]",
            0.00541000379473566,
        ),
        ("NSHM_v1.0.0", "PUY", "[dm0.7, bN[0.902, 4.6], C4.0, s0.28]", 0.21),
        (
            "NSHM_v1.0.4",
            "CRU",
            "[dmgeologic, tdFalse, bN[1.089, 4.6], C4.2, s1.41]",
            0.00286782725429677,
        ),
        ("NSHM_v1.0.4", "PUY", "[dm0.7, bN[0.902, 4.6], C4.0, s0.28]", 0.21),
    ],
)
def test_get_model_SourceLogicTreeBranch_as_node(
    client, model_version, branch_set_short_name, tag, weight
):
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
                sources {
                    ... on BranchInversionSource {
                        nrml_id
                    }
                }
            }

        }
    }
    """ % to_global_id(
        "SourceLogicTreeBranch", f"{model_version}:{branch_set_short_name}:{tag}"
    )
    executed = client.execute(QUERY)
    print(executed)
    assert executed["data"]["node"]["id"] == to_global_id(
        "SourceLogicTreeBranch", f"{model_version}:{branch_set_short_name}:{tag}"
    )

    assert executed["data"]["node"]["model_version"] == model_version
    assert executed["data"]["node"]["branch_set_short_name"] == branch_set_short_name
    assert executed["data"]["node"]["tag"] == tag
    assert executed["data"]["node"]["weight"] == weight
'''
