# Client query corpus — migration parity

Real-world GraphQL queries replayed against a deployed stage to catch **runtime**
regressions that SDL parity (`schema.legacy.graphql`) misses (runbook Phase 0
step 2 / Phase 3 step 7).

## Status

- **`weka__*.graphql`** — REAL production query, vendored from the weka UI relay
  artifacts (the only confirmed GraphQL client of this API).
- **`seed__*.graphql` / `smoke__*.graphql`** — derived from the test suite + the
  deploy smoke query; supplementary coverage.

Each file is one query, named `<client>__<purpose>.graphql`. The leading comment
records the calling component. Vendor real query *text* (do not live-fetch at test
time — that introduced a deploy-time dependency in toshi-api, PR #325).

## Client survey (2026-06-22)

Surveyed the five candidate client repos for queries against this model API:

| Repo | Verdict |
|---|---|
| `UI/weka` | ✅ **Client** — `LogicTreePageQuery` (`src/views/LogicTree/LogicTreePage.tsx`). Vendored as `weka__logic_tree_page.graphql`. The only real GraphQL consumer found. |
| `UI/kororaa` | ❌ Not this API — its `FaultModelControlsQuery` targets the **solvis** fault-model schema (`KORORAA_nzshm_model … source_logic_tree { fault_system_branches }`). |
| `MISC/nzshm-runzi` | ❌ Uses the **`nzshm-model` Python library directly** (7 import sites, e.g. `runzi/tasks/oq_hazard/*`). No GraphQL calls to this API. |
| `LIB/toshi-hazard-store` | ❌ Uses the **`nzshm-model` library directly** (4 import sites). |
| `API/solvis-graphql-api` | ❌ Uses the **`nzshm-model` library directly** (4 import sites); defines its own GraphQL schema. Not a client of this API. |

**Implication:** weka is effectively the sole external GraphQL client. `LogicTreePageQuery`
covers nearly the whole schema in one operation, so parity on it ≈ parity for real
traffic. Still worth a periodic re-survey before cutover in case new clients appear.

## How it's replayed

A CI job (added in Phase 3) executes each `*.graphql` here against the test-stage
deploy and asserts the response shape matches legacy (modulo `@deprecated` notices).
