"""HTTP integration tests for the FastAPI app (request → router → schema → response).

Validates the FastAPI/Strawberry wiring end-to-end, which the schema-level tests
don't exercise. Mangum (the Lambda adapter) wraps this same `app`.
"""

import pathlib

from fastapi.testclient import TestClient

from nshm_model_graphql_api.app import app

client = TestClient(app)


def test_post_query_returns_data():
    r = client.post("/graphql", json={"query": "{ about version current_model_version }"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["version"]
    assert data["current_model_version"]


def test_get_serves_graphiql():
    r = client.get("/graphql", headers={"accept": "text/html"})
    assert r.status_code == 200
    assert "graphiql" in r.text.lower()


def test_weka_query_over_http():
    query = (pathlib.Path(__file__).parent / "fixtures" / "corpus" / "weka__logic_tree_page.graphql").read_text()
    r = client.post("/graphql", json={"query": query, "variables": {"version": "NSHM_v1.0.4"}})
    assert r.status_code == 200
    body = r.json()
    assert body.get("errors") is None
    assert body["data"]["get_model"]["version"] == "NSHM_v1.0.4"
    assert body["data"]["get_model"]["gmm_logic_tree"]["branch_sets"]
