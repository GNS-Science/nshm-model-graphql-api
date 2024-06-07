import pytest
from graphene.test import Client

from nshm_model_graphql_api import schema

# from graphql_relay import to_global_id


@pytest.fixture(scope="module")
def client():
    return Client(schema.schema_root)


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_and_branch_sets(client, model_version):
    QUERY = (
        """
        query {
            get_model(version: "%s")
            {
                gmm_logic_tree {
                    branch_sets {
                        __typename
                        model_version
                        short_name
                        long_name
                        tectonic_region_type
                    }
                }
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
    branch_sets = executed["data"]["get_model"]["gmm_logic_tree"]["branch_sets"]
    assert branch_sets[0]["__typename"] == "GmmBranchSet"
    assert branch_sets[0]["model_version"] == model_version
    assert branch_sets[0]["tectonic_region_type"] == "Active Shallow Crust"
    assert branch_sets[0]["short_name"] == "CRU"
    assert branch_sets[0]["long_name"] == "Crustal"


@pytest.mark.parametrize(
    "model_version",
    [
        "NSHM_v1.0.4",
        "NSHM_v1.0.0",
    ],
)
def test_get_model_and_branch_set_branches(client, model_version):
    QUERY = (
        """
        query {
            get_model(version: "%s")
            {
                gmm_logic_tree {
                    branch_sets {
                        # short_name
                        branches {
                            __typename
                            # branch_set_short_name
                            model_version
                            weight
                            gsim_name
                            gsim_args
                        }
                    }
                }
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
    branch_sets = executed["data"]["get_model"]["gmm_logic_tree"]["branch_sets"]
    # assert branch_sets[0]["short_name"] == "PUY"
    assert branch_sets[0]["branches"][0]["weight"] <= 1.0
    assert branch_sets[0]["branches"][0]["gsim_name"] == "Stafford2022"
    assert branch_sets[0]["branches"][0]["gsim_args"] == "{'mu_branch': 'Upper'}"

    assert branch_sets[0]["branches"][0]["__typename"] == "GmmLogicTreeBranch"
    assert branch_sets[0]["branches"][0]["model_version"] == model_version
    # assert branch_sets[0]["branches"][0]["branch_set_short_name"] == "PUY"
