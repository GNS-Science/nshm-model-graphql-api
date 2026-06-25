"""Differential live driver — Phase 5 cutover validation (low-traffic strategy).

Model has almost no organic traffic, so a passive soak + CloudWatch baseline gives
no signal. Instead we ACTIVELY drive queries at the deployed `/graphql` and compare
each response **byte-for-byte against the in-process Strawberry schema** — the oracle,
already proven identical to the legacy schema (see tests/test_schema_parity.py). Any
difference is something the *deploy* introduced (packaging, serialization, env,
cold-start data load), which is exactly what we can't see from metrics here.

Coverage (enumerated, not sampled-from-traffic):
  - the no-variable corpus queries (root info, get_models, about),
  - for EVERY model version: the full weka tree query (get_model + both logic trees),
  - for every version: a node(id) lookup for each of the 7 Relay node types,
    using ids harvested from that version's tree.

Usage:
    uv run python tests/smoke/drive_live.py --url <stage-graphql-url> --api-key <key>
    SMOKE_URL=<stage-graphql-url> SMOKE_API_KEY=<key> uv run python tests/smoke/drive_live.py
    # restrict while iterating:
    uv run python tests/smoke/drive_live.py --url ... --only-version NSHM_v1.0.4

Exit 0 = every live response matched the oracle; non-zero on any diff/error.
"""

import argparse
import json
import os
import pathlib

os.environ.setdefault("TESTING", "1")  # keep app/library side effects quiet at import

import httpx  # noqa: E402

from nshm_model_graphql_api import data  # noqa: E402
from nshm_model_graphql_api.schema import schema  # noqa: E402

CORPUS_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "corpus"
FULL_QUERY = (CORPUS_DIR / "weka__logic_tree_page.graphql").read_text()
NODE_QUERY = (CORPUS_DIR / "seed__node_relay_lookup.graphql").read_text()
NO_VAR_CORPUS = ["smoke__about.graphql", "seed__root_info.graphql", "seed__get_models.graphql"]


def _harvest_ids(tree: dict) -> list[tuple[str, str]]:
    """Pull one global id per Relay node type out of a full-tree result."""
    out: list[tuple[str, str]] = []
    gm = (tree or {}).get("get_model")
    if not gm:
        return out
    out.append(("NshmModel", gm["id"]))
    slt = gm.get("source_logic_tree") or {}
    if slt.get("id"):
        out.append(("SourceLogicTree", slt["id"]))
    sbs = (slt.get("branch_sets") or [None])[0]
    if sbs:
        out.append(("SourceBranchSet", sbs["id"]))
        sb = (sbs.get("branches") or [None])[0]
        if sb:
            out.append(("SourceLogicTreeBranch", sb["id"]))
    gmt = gm.get("gmm_logic_tree") or {}
    if gmt.get("id"):
        out.append(("GroundMotionModelLogicTree", gmt["id"]))
    gbs = (gmt.get("branch_sets") or [None])[0]
    if gbs:
        out.append(("GmmBranchSet", gbs["id"]))
        gb = (gbs.get("branches") or [None])[0]
        if gb:
            out.append(("GmmLogicTreeBranch", gb["id"]))
    return out


class Driver:
    def __init__(self, url: str, api_key: str | None, timeout: float):
        self.url = url
        self.headers = {"content-type": "application/json"}
        if api_key:
            self.headers["x-api-key"] = api_key
        self.timeout = timeout
        self.checks = 0
        self.failures = 0

    def _oracle(self, query: str, variables: dict | None):
        res = schema.execute_sync(query, variable_values=variables)
        return res.data, [e.message for e in (res.errors or [])]

    def _live(self, query: str, variables: dict | None):
        resp = httpx.post(
            self.url, json={"query": query, "variables": variables}, headers=self.headers, timeout=self.timeout
        )
        body = resp.json()
        return resp.status_code, body.get("data"), body.get("errors")

    def check(self, label: str, query: str, variables: dict | None = None):
        self.checks += 1
        oracle_data, oracle_errs = self._oracle(query, variables)
        if oracle_errs:
            self._fail(label, f"ORACLE errored (bad query/fixture): {oracle_errs}")
            return None
        try:
            status, live_data, live_errs = self._live(query, variables)
        except Exception as exc:  # noqa: BLE001
            self._fail(label, f"request error: {exc}")
            return None
        if status != 200 or live_errs:
            self._fail(label, f"HTTP {status}, errors={live_errs}")
            return None
        if live_data != oracle_data:
            self._fail(label, "live != oracle", oracle_data, live_data)
            return None
        print(f"OK    {label}")
        return oracle_data

    def _fail(self, label, msg, oracle=None, live=None):
        self.failures += 1
        print(f"DIFF  {label}: {msg}")
        if oracle is not None:
            print(f"        oracle: {json.dumps(oracle)[:240]}")
            print(f"        live:   {json.dumps(live)[:240]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=os.environ.get("SMOKE_URL"), help="deployed /graphql URL")
    ap.add_argument("--api-key", default=os.environ.get("SMOKE_API_KEY"), help="x-api-key value")
    ap.add_argument("--only-version", help="restrict enumeration to a single model version")
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()
    if not args.url:
        ap.error("--url (or SMOKE_URL) is required")

    d = Driver(args.url, args.api_key, args.timeout)

    # 1) no-variable corpus queries
    for name in NO_VAR_CORPUS:
        d.check(f"corpus:{name}", (CORPUS_DIR / name).read_text())

    # 2) every model version: full tree + a node lookup per type
    versions = [args.only_version] if args.only_version else list(data.all_model_versions())
    print(f"\n-- enumerating {len(versions)} model version(s) --")
    for v in versions:
        tree = d.check(f"full_tree[{v}]", FULL_QUERY, {"version": v})
        if tree is None:
            continue
        for type_name, gid in _harvest_ids(tree):
            d.check(f"node[{v}]:{type_name}", NODE_QUERY, {"id": gid})

    ok = d.failures == 0
    print(f"\n{'✅ live matches oracle' if ok else f'❌ {d.failures} mismatch(es)'} — {d.checks} checks")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
