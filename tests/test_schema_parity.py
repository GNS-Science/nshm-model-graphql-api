"""Migration parity gate.

The Strawberry schema must stay SDL-identical to the committed Graphene baseline
(`schema.legacy.graphql`). Fails loudly on any drift (added/removed/retyped field,
changed nullability, lost description) — order is ignored.
"""

import pathlib

from graphql import build_schema, print_schema
from graphql.utilities import lexicographic_sort_schema

from nshm_model_graphql_api.schema import schema as strawberry_schema

BASELINE = pathlib.Path(__file__).parent.parent / "schema.legacy.graphql"


def _canonical(sdl: str) -> str:
    """Order-insensitive canonical SDL (sorts types/fields, normalizes formatting)."""
    return print_schema(lexicographic_sort_schema(build_schema(sdl)))


def test_strawberry_sdl_matches_committed_baseline():
    assert _canonical(BASELINE.read_text()) == _canonical(strawberry_schema.as_str())
