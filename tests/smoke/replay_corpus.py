"""Smoke test: replay the vendored client query corpus against a DEPLOYED stage.

Phase 5 cutover check (runbook Phase 5 step 3). Unlike `tests/test_corpus_replay.py`
(which runs the schema in-process during unit CI), this POSTs each corpus query to a
live `/graphql` URL with the API key, so it validates the real deploy: API Gateway →
Lambda → Mangum → FastAPI → Strawberry. Not collected by pytest (filename isn't
`test_*.py`); run it by hand against the test (and later prod) stage.

Usage:
    uv run python tests/smoke/replay_corpus.py --url <stage-graphql-url> --api-key <key>
    # or via env:
    SMOKE_URL=<stage-graphql-url> SMOKE_API_KEY=<key> uv run python tests/smoke/replay_corpus.py

Exit 0 = every query returned 200 with no GraphQL errors; non-zero otherwise.
"""

import argparse
import json
import os
import pathlib
import sys

import httpx
from graphql_relay import to_global_id

CORPUS_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "corpus"

# Variables for the queries that need them (mirrors tests/test_corpus_replay.py).
VARIABLES = {
    "weka__logic_tree_page.graphql": {"version": "NSHM_v1.0.4"},
    "seed__node_relay_lookup.graphql": {"id": to_global_id("NshmModel", "NSHM_v1.0.4")},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("SMOKE_URL"), help="deployed /graphql URL")
    parser.add_argument("--api-key", default=os.environ.get("SMOKE_API_KEY"), help="x-api-key value")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    if not args.url:
        parser.error("--url (or SMOKE_URL) is required")

    headers = {"content-type": "application/json"}
    if args.api_key:
        headers["x-api-key"] = args.api_key

    queries = sorted(CORPUS_DIR.glob("*.graphql"))
    if not queries:
        print("no corpus queries found", file=sys.stderr)
        return 1

    failures = 0
    for path in queries:
        payload = {"query": path.read_text(), "variables": VARIABLES.get(path.name)}
        try:
            resp = httpx.post(args.url, json=payload, headers=headers, timeout=args.timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {path.name}: request error: {exc}")
            failures += 1
            continue
        ok = resp.status_code == 200
        body = {}
        try:
            body = resp.json()
        except json.JSONDecodeError:
            ok = False
        if body.get("errors"):
            ok = False
        if ok and body.get("data") is None:
            ok = False
        status = "OK  " if ok else "FAIL"
        print(f"{status}  {path.name}  (HTTP {resp.status_code})")
        if not ok:
            failures += 1
            print(f"      -> {json.dumps(body)[:300]}")

    print(f"\n{'✅ smoke OK' if not failures else f'❌ {failures} smoke failure(s)'} ({len(queries)} queries)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
