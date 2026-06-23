"""Replay the vendored client query corpus against the Strawberry schema.

Catches runtime regressions that SDL parity can't (a query that validates but
errors at execution). The corpus includes the real weka `LogicTreePageQuery`,
which exercises nearly the whole schema in one operation.
"""

import pathlib

import pytest
from graphql_relay import to_global_id

from nshm_model_graphql_api.schema import schema

CORPUS_DIR = pathlib.Path(__file__).parent / "fixtures" / "corpus"
CORPUS = sorted(CORPUS_DIR.glob("*.graphql"))

# Variables for the queries that need them.
VARIABLES = {
    "weka__logic_tree_page.graphql": {"version": "NSHM_v1.0.4"},
    "seed__node_relay_lookup.graphql": {"id": to_global_id("NshmModel", "NSHM_v1.0.4")},
}


def test_corpus_is_not_empty():
    assert CORPUS, "no corpus queries found"


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.name)
def test_corpus_query_executes(path):
    result = schema.execute_sync(path.read_text(), variable_values=VARIABLES.get(path.name))
    assert result.errors is None, f"{path.name}: {result.errors}"
    assert result.data is not None
