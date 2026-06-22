"""Dump the legacy Graphene schema SDL to stdout.

Migration parity baseline (Phase 0 of the Graphene -> Strawberry migration).
The committed `schema.legacy.graphql` produced by this is the parity target:
anything removed from the new Strawberry SDL that is not marked `@deprecated`
is a breaking change.

Importing the schema pulls in dependencies (e.g. `nzshm-model`) that print
warnings to stdout at import time; we redirect that to stderr so only the SDL
lands on stdout and the output file stays valid.

Usage:
    uv run python -m nshm_model_graphql_api.tools.dump_legacy_sdl > schema.legacy.graphql
"""

import contextlib
import sys


def main() -> None:
    # Keep import-time chatter off stdout so the SDL file is clean.
    with contextlib.redirect_stdout(sys.stderr):
        from nshm_model_graphql_api.schema import schema_root

    print(str(schema_root), end="")


if __name__ == "__main__":
    main()
