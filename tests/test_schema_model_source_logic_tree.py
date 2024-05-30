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
                source_logic_tree {
                    branch_sets {
                        __typename
                        model_version
                        short_name
                        long_name
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
    branch_sets = executed["data"]["get_model"]["source_logic_tree"]["branch_sets"]
    assert branch_sets[0]["__typename"] == "SourceBranchSet"
    assert branch_sets[0]["model_version"] == model_version
    assert branch_sets[0]["short_name"] == "PUY"


@pytest.mark.parametrize(
    "model_version",
    ["NSHM_v1.0.0", "NSHM_v1.0.4"],
)
def test_get_model_and_branch_set_branches(client, model_version):
    QUERY = (
        """
        query {
            get_model(version: "%s")
            {
                source_logic_tree {
                    branch_sets {
                        short_name
                        branches {
                            __typename
                            model_version
                            weight
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
    branch_sets = executed["data"]["get_model"]["source_logic_tree"]["branch_sets"]
    assert branch_sets[0]["short_name"] == "PUY"
    assert branch_sets[0]["branches"][0]["weight"] <= 1.0
    assert branch_sets[0]["branches"][0]["__typename"] == "SourceLogicTreeBranch"
    assert branch_sets[0]["branches"][0]["model_version"] == model_version
