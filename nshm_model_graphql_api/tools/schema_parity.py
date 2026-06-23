"""SDL parity check: new Strawberry schema vs the committed legacy baseline.

Compares the live Strawberry schema against `schema.legacy.graphql` (the Graphene
baseline from Phase 0) in an order-insensitive way, so cosmetic type/field
ordering differences are ignored but any real change (added/removed/retyped field,
changed nullability, lost description) fails the check.

Usage:
    uv run python -m nshm_model_graphql_api.tools.schema_parity [path/to/schema.legacy.graphql]

Exit code 0 = identical, 1 = differences (unified diff printed to stderr).
"""

import contextlib
import difflib
import sys

DEFAULT_BASELINE = "schema.legacy.graphql"


def _canonical(sdl: str) -> str:
    from graphql import build_schema, print_schema
    from graphql.utilities import lexicographic_sort_schema

    return print_schema(lexicographic_sort_schema(build_schema(sdl)))


def main(argv: list[str]) -> int:
    baseline_path = argv[1] if len(argv) > 1 else DEFAULT_BASELINE

    # Keep import-time chatter (nzshm-model warning) off stdout.
    with contextlib.redirect_stdout(sys.stderr):
        from nshm_model_graphql_api.schema import schema

    with open(baseline_path) as f:
        legacy = _canonical(f.read())
    new = _canonical(schema.as_str())

    if legacy == new:
        print("✅ SDL parity: new schema matches the legacy baseline.")
        return 0

    print("❌ SDL parity FAILED — new schema differs from the legacy baseline:", file=sys.stderr)
    sys.stderr.writelines(
        difflib.unified_diff(
            legacy.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=baseline_path,
            tofile="strawberry_schema",
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
