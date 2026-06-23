# Graphene → Strawberry Migration Log — `nshm-model-graphql-api`

**This API is the pilot migration** for the Graphene 3 / Flask / serverless-wsgi → Strawberry / FastAPI / Mangum effort across the four GraphQL siblings.

**Authoritative runbook:** [`../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md`](../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md)
(reference migration: `nshm-toshi-api`, completed 2026-06). Read it first — this log only records **what is specific to this repo** and **what actually happened** here. Per the runbook's "Maintenance" rule, every surprise found here must be folded back into that runbook (one-line note or new trap), and this API MUST file at least one PR against it.

- **Owner:** Chris B Chamberlain (chrisbc@artisan.co.nz)
- **Migration branch:** `migrate/strawberry` (based on `deploy-test`)
- **Started:** 2026-06-22
- **Status:** Phase 4 — Deploy/CI/deps hardening 🟡 in progress (2026-06-23): deploy-packaging resolved; vuln fixes **held** pending approval; real deploy proof deferred to Phase 5.
- **PRs:** stacked, one per phase — #63 (P0), #64 (P1), #65 (P2), #66 (P3), #67 (P4). Base chain: `deploy-test` ← P0 ← P1 ← P2 ← P3 ← P4.
- **Why this one first** (runbook §A1): smallest (~7 .py files), zip Lambda, no DynamoDB writes, no auth, minimal external integrations — lowest blast radius. The heavy `nzshm-model` library stays untouched.

---

## Repo-specific facts (Phase 0 inventory)

Captured up front so the plan is grounded in what actually exists. Source: code exploration 2026-06-22.

### Current stack
- **Python** 3.12 (`>=3.12,<4.0`), **Node** 22, **Yarn** 4.14.1, **uv** for Python deps (poetry already dropped — `uv.lock` present).
- **GraphQL:** `graphene>=3.3` + `graphql-server==3.0.0b7` (pinned pre-release) served via Flask + `flask-cors`.
- **Serverless:** Framework v4, single plugin `serverless-wsgi`; `serverless-plugin-warmup` present in deps but **commented out** in `serverless.yml`.
- **Handler:** `wsgi_handler.handler` → `nshm_model_graphql_api.nshm_model_graphql_api.app`.
- **Service:** `nzshm22-model-graphql-api`, region `ap-southeast-2`, **memory 2048 MB**, **timeout 10 s**, runtime `python3.12`.

### App / schema layout (`nshm_model_graphql_api/`)
| File | Role |
|---|---|
| `nshm_model_graphql_api.py` | Flask app factory `create_app()`; registers `/graphql` `GraphQLView` (GraphiQL on); module-level `app` for WSGI |
| `schema/__init__.py` | re-exports `schema_root` |
| `schema/schema_root.py` | `QueryRoot` + `graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)` (line ~48) |
| `schema/nshm_model_schema.py` | `NshmModel` (relay.Node); nested `source_logic_tree`, `gmm_logic_tree`; wraps `nzshm-model` |
| `schema/nshm_model_sources_schema.py` | `SourceLogicTree` → `SourceBranchSet` → `SourceLogicTreeBranch`; union `BranchSource` = `BranchInversionSource` \| `BranchDistributedSource` |
| `schema/nshm_model_gmms_schema.py` | `GroundMotionModelLogicTree` → `GmmBranchSet` → `GmmLogicTreeBranch` |

### Schema contract to preserve
- **Query-only**, no mutations → the runbook's `ClientIDMutation`/payload traps **do not apply**.
- **`auto_camelcase=False`** today → new schema MUST use `StrawberryConfig(auto_camel_case=False)` (runbook Trap #2). All fields are snake_case (`get_models`, `get_model(version)`, `current_model_version`, `source_logic_tree`, `gmm_logic_tree`, `model_version`, `short_name`, `long_name`, `branch_set_short_name`, `tectonic_region_type`, `gsim_name`, `gsim_args`, `nrml_id`, `rupture_set_id`, `inversion_id`).
- **7 Relay Node types**, each with custom `resolve_id` + `get_node`. Composite IDs by string concat with **per-type delimiters** — carry these forward exactly:
  - `NshmModel`: `{version}`
  - `SourceLogicTree` / `GroundMotionModelLogicTree`: `{model_version}`
  - `SourceBranchSet` / `GmmBranchSet`: `{model_version}:{short_name}`
  - `SourceLogicTreeBranch`: `{model_version}:{branch_set_short_name}:{tag}`
  - `GmmLogicTreeBranch`: `{model_version}|{branch_set_short_name}|{gsim_name}|{json(gsim_args)}` (pipe-delimited)
- **One union:** `BranchSource`. **One JSON scalar:** `gsim_args` (graphene `JSONString`).
- **Two field descriptions only** (`about`, `version` on root) — otherwise undocumented.
- **No `@deprecated` / `deprecation_reason` anywhere** → runbook's deprecated-field forward-port traps (#7, #8) are N/A for the pilot, but keep the grep discipline.

### Data source
- All data from the **`nzshm-model>=0.14.0`** library (no persistence layer). Entry points: `nm.all_model_versions()`, `nm.get_model_version(v)`, `nm.CURRENT_VERSION`.
- Heavy use of `@functools.lru_cache` on module-level getters (`get_model_by_version`, `get_branch_set`, `get_logic_tree_branch`). Cache keys are strings → safe to carry over.
- `uv` config keeps `nzshm-model` resolving to latest (`exclude-newer-package."nzshm-model" = false`).

### Tests
- `tests/` — 8 files (~660 LOC), ~22–28 assertions, **no `conftest.py`**, no snapshots, no moto/testcontainers, fully local (no AWS).
- All use `graphene.test.Client(schema.schema_root)` (module-scoped fixture per file) → must move to a Strawberry test client.
- Coverage surface: root info fields, `get_models`/`get_model`, nested source & gmm logic trees, and `node(id)` Relay lookups for all 7 types with inline fragments. `moto>=5.1` is in dev deps but **unused**.
- `TESTING=1` is set by tox `[testenv]`, not via conftest.

### Deploy / CI / secrets
- **Auth:** API Gateway **API key** only (`TempApiKey-${stack_name}`), `private: true` on the POST route; GET (GraphiQL) public. **No `LEGACY_API_KEY` / `x-api-key` env chain** in this repo → runbook §4.3 trap is N/A (the auth contract here is the API-Gateway key, preserve that).
- `provider.environment`: `REGION`, `DEPLOYMENT_STAGE`; function env `STACK_NAME`. IAM: single `cloudwatch:PutMetricData` allow.
- **Routes to preserve:** `POST /graphql` (private), `GET /graphql`, `GET /graphql/{proxy+}`, `OPTIONS /graphql`, `GET /static/{proxy+}`.
- **Secrets / environments (⚠️ delta from runbook §4.2):** this repo does **NOT** use the `AWS_TEST` / `AWS_PROD` GitHub Environments the runbook assumes. Instead:
  - **Repo-level secrets:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (static keys, created 2024-06), `SERVERLESS_ACCESS_KEY`, `CODECOV_TOKEN`, `SCHEDULED_GITHUB_SLACK_WEBHOOK`.
  - **One environment, `DEPLOY_TEST`, with no environment-level secrets.** Deploy auth resolves from the repo-level static AWS keys + `SERVERLESS_ACCESS_KEY`.
  - Implication: no OIDC role / per-env secret split to preserve. If migrating toward the runbook's posture is desired, that's a separate hardening task — out of scope for the code migration. Capture as runbook feedback (the four siblings may not share the AWS_TEST/AWS_PROD assumption).
- CI uses **shared reusable workflows** from `GNS-Science/nshm-github-actions`:
  - `dev.yml` — tests; trigger `pull_request: branches: [main, deploy-test]` (⚠️ runbook Trap #14 — this `branches:` filter silently skips CI on stacked PRs; remove it).
  - `deploy-to-aws.yaml` — push to `deploy-test` or `main`; runs tests then deploys (Node 22 / Yarn; smoke query `query QueryRoot{about}`).
  - `release.yml` — on `v*` tags; PyPI publish disabled.
- `.yarnrc.yml` already has `nodeLinker: node-modules`, `npmMinimalAgeGate: 7d`, preapproved scopes (`nshm-*`, `nzshm-*`, `solvis-*`, `weka-*`, `toshi-*`) — matches runbook §4.6.
- `setup.cfg` holds pytest + coverage + tox (`audit`, `py312`, `format`, `lint`, `build`); no standalone `tox.ini`.
- `.bumpversion.cfg` syncs version across `pyproject.toml`, `package.json`, `__init__.py` (currently **0.4.2**).

### Branch hygiene (done 2026-06-22, pre-migration)
- Local `main` fast-forwarded (was 63 behind), stale `chore/50-migrate-to-serverless-v4` deleted, refs synced to origin.
- Removed obsolete `package-lock.json` from `deploy-test` (`d9d667b`) — Yarn 4 project, `main` had already dropped it. Remaining `main`↔`deploy-test` delta is content-duplicate (squash + the same package-lock delete) and collapses on the next promote.
- ⚠️ Dependabot reports **15 vulnerabilities** (7 high / 6 moderate / 2 low) on the default branch — review during Phase 4 deps hardening; `upgrades (#61)` may already cover some.

---

## Deltas from the runbook (what does / doesn't apply here)

| Runbook item | Applies? | Note |
|---|---|---|
| `StrawberryConfig(auto_camel_case=False)` (Trap #2) | ✅ Yes | snake_case schema today |
| FastAPI + Mangum entry, drop `serverless-wsgi` | ✅ Yes | handler → `<pkg>.app.handler` |
| Drop poetry → uv | ☑️ Already done | `uv.lock` present |
| Lint-config consolidation (Trap #3) | ⚠️ Watch | small tree; current ruff already `E,F,I,B,UP` |
| Layered models / `_dispatch.py` (Traps #4–6) | ❌ No | only 7 types, static union; no `clazz_name` dispatch |
| `ClientIDMutation` payload shape (Trap, Phase 2) | ❌ No | query-only API |
| Deprecated field carry-forward (Traps #7–8) | ❌ N/A | none exist; keep grep discipline |
| `LEGACY_API_KEY` chain (Trap #11, §4.3) | ❌ No | API-Gateway key only; preserve that instead |
| `DB_READ_ONLY` (Trap #12) | ❌ No | no DB |
| testcontainers / DynamoDB Local / Java (Trap #10) | ❌ No | tests fully local; moto already available if needed |
| Remove `pull_request.branches:` filter (Trap #14) | ✅ Done | removed in P0 branch — stacked PRs were getting no CI until then |
| Yarn `resolutions` / local-dev plugin traps (§4.7, #16–17) | ⚠️ Low | only `serverless-wsgi` plugin (being removed); no s3rver/dynamodb-local |
| Lambda memory halve-and-monitor (§4.4, #20) | ✅ Yes | 2048 MB → start at 1024 MB, watch CloudWatch |
| SDL parity + query corpus replay (Phase 0/3) | ✅ Yes | no corpus today — vendor real queries from tests + clients |
| 24h soak before promote (Phase 5) | 🔁 Optional | runbook says Model is the candidate to skip (low traffic) |

---

## Planned phase checklist (tailored)

> Full detail in the runbook. This is the repo-specific tracking list — tick as completed and append a dated note under "Log entries" for each.

### Phase 0 — Pre-flight ✅
- [x] Dump legacy Graphene SDL → `schema.legacy.graphql` (116 lines; tool: `nshm_model_graphql_api/tools/dump_legacy_sdl.py`), committed as parity target
- [x] Seed a client query corpus in `tests/fixtures/corpus/` (6 queries, all validate against legacy schema) — ⚠️ still need to chase **real** `runzi`/frontend queries (see corpus README)
- [x] Inventory secrets — found repo-level static AWS keys + `DEPLOY_TEST` env (NOT `AWS_TEST`/`AWS_PROD`); see delta note above

### Phase 1 — Bootstrap (zip Lambda) ✅
- [x] Add deps: `strawberry-graphql` (0.316), `fastapi` (0.137), `mangum` (0.21), `pydantic`, `httpx` (dev); `uv lock && uv sync` (frozen-consistent)
- [x] `nshm_model_graphql_api/app.py` — FastAPI + `GraphQLRouter` (prefix `/graphql`) + `Mangum` handler
- [x] `nshm_model_graphql_api/strawberry_schema.py` — `Schema(query=Query, config=StrawberryConfig(auto_camel_case=False))` ⚠️ named `strawberry_schema.py` not `schema.py` (legacy `schema/` **package** still occupies that name; rename at cutover). **Minimal Query only** (scalar root fields) — full type tree is Phase 2.
- [x] `serverless.yml` — `plugins: []` (dropped `serverless-wsgi`); removed `custom.wsgi`; handler → `nshm_model_graphql_api.app.handler`; memory 2048 → 1024
- [x] Verify boot: HTTP `TestClient` POST `/graphql` → 200 + correct data; GET `/graphql` → GraphiQL. SDL snake_case confirmed (`current_model_version`, not camelCase). ruff/mypy clean; 39 tests still pass.

### Phase 2 — Schema migration (the 7 types) ✅
- [x] `nshm_model_graphql_api/data.py` — graphene-free data layer over nzshm-model dataclasses (mirrors legacy helpers)
- [x] `NshmModel` + root `QueryRoot` (`get_models`, `get_model`, `about`, `version`, `current_model_version`, `node`)
- [x] Source tree: `SourceLogicTree` → `SourceBranchSet` → `SourceLogicTreeBranch` + `BranchSource` union (both members)
- [x] GMM tree: `GroundMotionModelLogicTree` → `GmmBranchSet` → `GmmLogicTreeBranch`
- [x] **Custom** `Node` interface (NOT `strawberry.relay`) — keeps `id: ID!` + exact `graphql_relay` base64 encoding; per-type composite-ID schemes + `node()` dispatch table preserved
- [x] `gsim_args` `JSONString` scalar parity (custom strawberry scalar, json.dumps/loads, exact description)
- [x] **SDL parity ✅ + runtime parity ✅** vs legacy (see below); ruff/mypy clean; 39 legacy tests still pass

### Phase 3 — Tests ✅
- [x] `tests/conftest.py` — **parametrized `client` fixture** (legacy Graphene + Strawberry) with a `.execute()` shim; the 7 existing schema-test files now run against **both** schemas (their local fixtures removed)
- [x] `tests/test_schema_parity.py` — SDL parity gate (strawberry vs committed baseline AND vs live legacy)
- [x] `tests/test_corpus_replay.py` — every vendored corpus query executes on Strawberry with no errors
- [x] `tests/test_strawberry_http.py` — FastAPI `TestClient` happy-path + GraphiQL + weka query over HTTP
- [x] testcontainers **not needed** (read-only, fully local) — runbook Trap #10 N/A here
- [x] Parity + corpus run inside `pytest`, so they're already in CI (shared `python-run-tests-uv` workflow); **87 tests pass**

### Phase 4 — Deploy / CI / deps 🟡
- [x] Remove `branches:` filter in `dev.yml` (Trap #14) — done in P0
- [x] **Lambda dep packaging** (the Phase 1 open question) — resolved: SF v4 has **built-in** python-requirements (activated by `custom.pythonRequirements`, uv-aware). `serverless-wsgi` had been doing this; removing it doesn't break packaging. `deploy` script generates `requirements.txt` from uv; `serverless-wsgi` removed from `package.json`.
- [x] Confirm API-Gateway key auth unchanged + `/graphql` (+ `static`) routes preserved — verified in `serverless.yml`
- [x] `uv sync --frozen` in CI — handled by shared `python-run-tests-uv` workflow; lock is frozen-consistent
- [x] Memory 1024 MB set (P1); CloudWatch watch deferred to post-deploy (Phase 5)
- [ ] **Address vulns — deferred to a separate deps PR after the stack lands** (decision 2026-06-23): `urllib3` 2.6.3→2.7.0, `idna` 3.11→3.15, `lxml` 6.0.4→6.1.0 (6 advisories, all transitive)
- [ ] **Final packaging proof = Phase 5 test-stage deploy** (local `sls package` blocked by SF v4 mandatory AWS account resolution)

### Phase 5 — Cutover 🟡 (TEST done; prod held)
- [x] **Pre-staged:** rollback runbook + draft-revert-PR template + triggers, **differential live driver**, manual-weka + promote plan → [`PHASE5_CUTOVER.md`](PHASE5_CUTOVER.md) + `tests/smoke/drive_live.py`
- [x] **Strategy: active differential validation, not soak** (traffic too low for a metric baseline). Driver replays enumerated queries (every model version + all 7 node types) at the live `/graphql` and diffs byte-for-byte vs the in-process oracle. Validated in-process (19 checks, 0 mismatches).
- [x] **Merged P0–P4 to `deploy-test` → DEPLOYED TO TEST** (2026-06-23): one combined merge (#67 carrying #63–#66) → single deploy run **success**. **Phase 4 packaging proven for real**: SF v4 built-in python-requirements packaged the deps; deploy smoke `{about}` passed. `drive_live` vs the deployed Strawberry app = **19/19 match**.
- [ ] Manual weka exercise against test (point weka at the test endpoint, drive Logic Tree view)
- [ ] **HOLD** — deps PR (#68) + P5 docs PR (#69) not merged; prod not promoted (awaiting go-ahead)
- [ ] Promote `deploy-test → main`; open draft revert PR with merge SHA; run driver+weka vs prod; ~30-min log watch
- [ ] Post-healthy cutover cleanup: delete legacy `schema/` + Flask app + legacy deps + `legacy` test param; rename `strawberry_schema.py` → `schema.py`

---

## Log entries

### 2026-06-22 — kickoff
- Synced local branches with origin; deleted stale `chore/50-…v4`; forward-ported `package-lock.json` deletion to `deploy-test` (`d9d667b`).
- Created branch `migrate/strawberry` off `deploy-test`.
- Created this log; captured Phase 0 inventory and runbook deltas above.
- **Next:** Phase 0 — dump legacy SDL + vendor query corpus.

### 2026-06-22 — Phase 0 complete
- Added `nshm_model_graphql_api/tools/dump_legacy_sdl.py`; committed `schema.legacy.graphql` (116 lines) as the parity target.
- Seeded `tests/fixtures/corpus/` with 6 queries (smoke `{about}`, root info, get_models, source tree w/ `BranchSource` union, gmm tree w/ `gsim_args`, Relay `node` lookup). All validate against the legacy schema.
- Inventoried secrets/environments → recorded the `AWS_TEST`/`AWS_PROD` delta (this repo uses repo-level static keys + a `DEPLOY_TEST` env).
- Baseline test suite green: **39 passed**.
- **Runbook feedback candidates (file against `nshm-toshi-api`):**
  1. *New trap:* the SDL-dump import path can print dependency warnings to **stdout** (here `nzshm-model` emits `WARNING: optional 'toshi' dependencies are not installed`), polluting `schema.legacy.graphql`. Fix: redirect stdout→stderr around the schema import (see `dump_legacy_sdl.py`). Runbook's Phase 0 snippet (`print(str(schema))`) doesn't guard this.
  2. *Phase 0 / §4.2 clarification:* secrets may **not** follow the `AWS_TEST`/`AWS_PROD` Environments pattern — Model uses repo-level static AWS keys + a single `DEPLOY_TEST` env. Runbook should not assume the OIDC/per-env split universally.
- **Next:** Phase 1 — add `strawberry-graphql`/`fastapi`/`mangum`/`pydantic`, create `app.py` + `schema.py`, swap `serverless.yml` handler, verify boot.

### 2026-06-22 — client query survey (Phase 0 corpus hardening)
Surveyed the five candidate client repos (weka, kororaa, runzi, toshi-hazard-store, solvis-graphql-api) for real queries against this API:
- **weka is the only GraphQL client.** Vendored its real relay query `LogicTreePageQuery` → `tests/fixtures/corpus/weka__logic_tree_page.graphql` (covers `get_model` + both logic trees + the `BranchSource` union (both members) + `current_model_version` + `get_models` in one op). Endpoint: `…/weka-app-api/graphql` (dev points at the model API on `localhost:5000`).
- **kororaa** targets the **solvis** fault-model schema (`KORORAA_nzshm_model … source_logic_tree { fault_system_branches }`), not this API.
- **runzi (7), toshi-hazard-store (4), solvis-graphql-api (4)** all consume the **`nzshm-model` Python library directly** — no GraphQL calls to this API.
- All 7 corpus queries validate against `schema.legacy.graphql`. Full survey table in `tests/fixtures/corpus/README.md`.
- **Takeaway:** parity on `LogicTreePageQuery` ≈ parity for real external traffic. Re-survey before cutover in case new clients appear.
- *(Tooling note: Explore subagents are sandboxed to this repo and can't read sibling repos — had to run the cross-repo search directly. zsh doesn't word-split unquoted `$vars`; use `$=var` or pass paths literally to `rg`.)*

### 2026-06-22 — Phase 1 complete
- Added the Strawberry/FastAPI/Mangum stack to `pyproject.toml` deps (kept legacy Graphene/Flask deps alongside — removed at cutover). `uv.lock` regenerated; `uv sync --frozen` passes.
- New scaffold: `app.py` (FastAPI + Mangum, `/graphql` preserved) and `strawberry_schema.py` (minimal Query, `auto_camel_case=False`). Legacy Flask/Graphene app untouched and still passing.
- `serverless.yml`: removed `serverless-wsgi` plugin + `custom.wsgi`, handler → Mangum, memory 2048→1024.
- Verified end-to-end via FastAPI `TestClient`: POST `/graphql` 200 w/ correct data, GET `/graphql` serves GraphiQL.
- **Decisions / surprises:**
  1. Could **not** use `schema.py` (runbook's target name) — the legacy Graphene code lives in a `schema/` **package** that occupies that import path. Used `strawberry_schema.py` during transition; rename to `schema.py` at cutover once `schema/` is deleted. *(Runbook feedback: the `<pkg>/schema.py` instruction assumes the legacy schema isn't already a package named `schema`.)*
  2. Strawberry defaults output fields from `-> str` to **non-null** (`String!`); legacy graphene `String` is **nullable**. Annotated scalar resolvers `-> str | None` to match legacy SDL exactly (don't tighten the contract mid-migration). Watch this for every Phase 2 field.
  3. **Deploy packaging open question (Phase 4):** with `serverless-wsgi` gone, confirmed nothing yet validates how Python deps land in the Lambda zip (no `serverless-python-requirements` in `plugins`; `package.json` has `serverless requirements` scripts; SF v4 may package natively). Flagged inline in `serverless.yml`. Not blocking — branch isn't deployed until Phase 5.
- **Next:** Phase 2 — port the 7 types (`NshmModel`, source tree + `BranchSource` union, gmm tree) and the Relay `Node` interface into `strawberry_schema.py` / a `models/` layout, preserving the per-type composite-ID delimiter schemes and the `gsim_args` JSON scalar.

### 2026-06-22 — Phase 2 design note: reuse nzshm-model dataclasses as the data layer
Investigated whether `nzshm-model` (v0.15.0) exposes a schema we could import/extend instead of reproducing types.
- **No GraphQL schema upstream.** The library uses plain stdlib `@dataclass` (deserialized via `dacite`); declares no `graphene`/`strawberry`/`pydantic` deps (only `dacite`, `lxml`, `nzshm-common`). Nothing GraphQL-shaped to inherit.
- **The dataclasses ARE a usable data layer** (`nzshm_model.logic_tree.logic_tree_base.BranchSet`, `branch.Branch`, `source_logic_tree.logic_tree.{SourceBranch,SourceBranchSet,SourceLogicTree,InversionSource,DistributedSource}`, `gmcm_logic_tree.logic_tree.{GMCMBranch,GMCMBranchSet,GMCMLogicTree}`).
- **But our GraphQL types are a deliberate projection, not 1:1** — so we can't expose the dataclasses directly:
  - inject `model_version` / `branch_set_short_name` (not on the dataclass; threaded from context)
  - `tag`, `tectonic_region_type` come from dataclass `@property`s
  - `gsim_args` is JSON-serialized from `Dict`
  - `BranchInversionSource` exposes 3 of `InversionSource`'s 6 fields; `BranchDistributedSource` 1 of 3
  - Relay composite `id` is GraphQL-only
  - Auto-deriving would leak `rupture_rate_scaling`/`type`/`inversion_solution_type`/`values`/`tectonic_region_types`/`branch_id`/`logic_tree_version` and break SDL parity.
- **Decision:** hand-write the 7 Strawberry types as thin projections whose resolvers read the nzshm-model dataclasses (mirrors the legacy graphene code, preserves parity). Import the dataclasses for resolver type-hints; **skip building a separate pydantic data layer** — the upstream dataclasses already are it.
- **Runbook feedback candidate:** Phase 2's "keep DynamoDB shapes in `data/models.py` as pydantic BaseModel" assumes you own the data layer. When the upstream library already provides typed dataclasses (Model's case — and likely Solvis's PynamoDB→? path differs), reuse them rather than mirroring into pydantic.

### 2026-06-22 — Q&A: would pydantic upstream have changed the approach?
Considered whether the migration would differ if `nzshm-model` exposed pydantic models instead of dataclasses.
- **Marginally.** Strawberry has `strawberry.experimental.pydantic.type` (no dataclass equivalent) → could auto-generate types with explicit field selection (clean subset exposure + free validation). Dataclasses give no such hook → hand-write.
- **But the hard parts are data-layer-agnostic:** injected fields (`model_version`, `branch_set_short_name`), transforms (`gsim_args` JSON, `tag`/`tectonic_region_type` from `@property`), Relay composite IDs, the union, `auto_camel_case=False`/nullability parity — all still custom regardless.
- **Telling signal:** toshi-api *had* pydantic and deliberately did NOT use `experimental.pydantic` — kept pydantic in the data layer and hand-wrote Strawberry types + `from_dict` (integration is experimental + sharp edges with `strawberry.lazy`/cyclic types, which this schema has; and keeps data migrations isolated from schema migrations).
- **Conclusion:** approach is identical either way for this API — hand-written thin projection types over a typed data layer. Validation buys little (read-only data; `dacite` already validates). Decision unchanged.

### 2026-06-22 — Phase 2 complete (schema migration)
Ported all 7 types + union + JSONString scalar + root query to Strawberry, at strict parity.
- **New files:** `data.py` (data layer over nzshm-model dataclasses), `tools/schema_parity.py` (order-insensitive SDL parity gate). `strawberry_schema.py` is now the full schema; `app.py` already serves it.
- **SDL parity = byte-identical** to `schema.legacy.graphql` (compared via `lexicographic_sort_schema` → `print_schema`, so order is ignored but any field/type/nullability/description change fails). `uv run python -m nshm_model_graphql_api.tools.schema_parity` → ✅.
- **Runtime parity = byte-identical** output between legacy graphene and new strawberry for all corpus queries (incl. the real weka query) **and** `node(id)` round-trips for all 7 node types — global-id base64 encodings match exactly.
- **Key decisions / surprises (runbook feedback candidates):**
  1. **Used a custom `Node` interface, not `strawberry.relay`.** Strawberry's relay emits a `GlobalID` scalar and `id: GlobalID!`, which breaks SDL parity (`id: ID!`) and could change the wire id. A custom `@strawberry.interface Node` with `id: strawberry.ID` + `graphql_relay.to_global_id/from_global_id` reproduces graphene exactly. *(Runbook Phase 2 shows `relay.Node`/`relay.NodeID` — note the GlobalID-vs-ID parity gotcha for any API migrating an existing graphene relay schema. Composite IDs from multiple fields also don't fit `relay.NodeID[str]` cleanly.)*
  2. **`Optional[x] = None` args render as `arg: T = null`;** legacy graphene emits `arg: T`. Use `strawberry.UNSET` as the default to suppress it (fixed `get_model(version)`).
  3. **Output `-> str` becomes `String!`;** must annotate `-> str | None` to match graphene's nullable defaults (applies to every field — done).
  4. Custom scalar (`JSONString`) trips mypy `valid-type`; one `# type: ignore[valid-type]`. Global-id args typed `str | None` → coerce via f-string (matches graphql_relay's own f-string coercion) to satisfy mypy without changing output.
  5. Added `graphql-relay>=3.2` as an explicit dep (was transitive via graphene) so id encoding survives graphene removal at cutover.
- **Next:** Phase 3 — port the test suite to the Strawberry schema (currently tests target legacy `schema_root`), wire `tools/schema_parity.py` + corpus replay into CI.

### 2026-06-23 — stacked PRs + Phase 3 complete
- **Restructured the single `migrate/strawberry` branch into 3 stacked PRs** (one per phase) via cherry-pick: #63 P0 → `deploy-test`, #64 P1 → P0, #65 P2 → P1. P2's tree is byte-identical to the old branch (only log entry ordering differs). Original `migrate/strawberry` left on origin as a backup.
- **Trap #14 bit us live:** PRs #64/#65 (base = feature branch) got **no CI** until I removed the `branches: [main, deploy-test]` filter from `dev.yml` (committed on P0, cascade-rebased P1/P2). After that all three PRs ran tests and **passed**. (For same-repo PRs the head branch's workflow runs, so the fix had to be on every head branch → cascade.)
- **Phase 3 (this branch, #66 → P2):** parametrized `client` fixture runs the 7 existing schema-test files against **both** schemas; added parity / corpus-replay / HTTP tests. **87 pass**, ruff/mypy clean.
- **Follow-ups (Phase 4):** (1) `strawberry.scalar(NewType(...))` emits a DeprecationWarning ("use `StrawberryConfig.scalar_map`") — defer; changing it risks the `JSONString` SDL name/description, and CI ignores warnings. (2) `mangum` "no current event loop" warning on import — benign.
- **Next:** Phase 4 — deploy/CI/deps hardening (validate Lambda dep packaging without serverless-wsgi; Dependabot vulns; memory watch).

### 2026-06-23 — Phase 4 (deploy/CI/deps) — packaging resolved, upgrades held
- **Biggest finding — Lambda dep packaging.** Inspected the prior `.serverless/` artifact: the deployed zip contained `wsgi_handler.py` + all deps, and a `.serverless/requirements.txt`. So **`serverless-wsgi` (or rather SF's requirements step) packaged the Python deps**, and the package `patterns` (`!**` + `nshm_model_graphql_api/**`) only scope the *source*. The real mechanism: **Serverless Framework v4 ships python-requirements built-in**, activated by the presence of `custom.pythonRequirements` (SF prints this explicitly), and it's **uv-aware**. So removing `serverless-wsgi` does NOT break dep packaging — the built-in still runs. *(This retires the Phase-1 "deploy packaging open question.")*
- **Changes:** `serverless.yml` plugins emptied (built-in needs no plugin; kept `custom.pythonRequirements` with `dockerizePip`/`slim`/`noDeploy: botocore`); `package.json` `deploy` script now runs `export_requirements` (uv → `requirements.txt`) before `serverless deploy`; removed dead `serverless-wsgi` dep; `.gitignore` += `.serverless/` (`requirements.txt`/`audit.txt` already ignored).
- **Local validation limit:** `sls package` reaches packaging but SF v4 **always resolves the AWS account ID** (even offline, even without `org`/`app`), so a full local zip build isn't possible without creds. Plugin/config init validated; the built-in python-requirements message confirms it's active. **Definitive proof = Phase 5 test-stage deploy** (the legacy artifact already proves the mechanism).
- **Auth/routes:** unchanged — API-Gateway key on `POST /graphql` (`private: true`), public GET/GraphiQL, `/graphql` + `/graphql/{proxy+}` + `static/{proxy+}` all preserved. No `LEGACY_API_KEY` chain here (N/A).
- **Vuln audit (pip-audit, runtime deps): 6 advisories in 3 transitive packages** — `urllib3` 2.6.3→2.7.0 (PYSEC-2026-141/142), `idna` 3.11→3.15 (PYSEC-2026-215), `lxml` 6.0.4→6.1.0 (PYSEC-2026-87). **Upgrades HELD** per instruction — recommend a focused deps-bump (likely a separate PR) once approved.
- **Decision to revisit:** `deploy` generates `requirements.txt` explicitly even though the built-in is uv-aware — kept for determinism/portability; if Phase 5 shows the built-in prefers `uv.lock`, drop the generation.
- 87 tests pass; `yarn install --immutable` clean.
- **Next:** get approval on the vuln bumps; then Phase 5 — deploy to test stage (the packaging proof), run corpus + smoke, soak, promote.

### 2026-06-23 — Phase 5 pre-staged (deploy still pending)
Cutover assets prepared on `migrate/strawberry-p5-cutover` (stacked on the deps-bump branch):
- `docs/PHASE5_CUTOVER.md` — confirms **in-place replacement** (same stack/function/routes/URL; rollback = redeploy previous code), with: §1 rollback (test + prod, draft-revert-PR template, trigger criteria), §2 smoke, §3 soak (baseline + short soak; Model is the soak-skip candidate), §4 promote & 30-min prod watch + post-healthy cleanup list.
- `tests/smoke/replay_corpus.py` — replays the full corpus against a live deployed URL+API key (not collected by unit pytest); this is the **real packaging proof** deferred from Phase 4.
- Vuln-bump deps PR (#68) done earlier today; `pip-audit` clean.
- **Not yet done (needs AWS creds + go-ahead):** capture baseline, deploy to test, smoke, soak, promote.

### 2026-06-23 — Phase 5 validation strategy pivot (low traffic)
- Model's traffic is too low for a passive soak / CloudWatch baseline to mean anything, so swapped the strategy to **active differential validation**:
  - `tests/smoke/drive_live.py` — drives the live `/graphql` and compares each response **byte-for-byte against the in-process schema oracle** (proven == legacy). Enumerates every model version + a `node(id)` per Relay type per version, plus no-var corpus queries. (Replaces the simpler `replay_corpus.py`.)
  - **Manual weka exercise** — point weka at the deployed API, drive the Logic Tree view (the real `LogicTreePageQuery`).
  - CloudWatch demoted to a quick glance (Errors/Throttles ≈ 0; one `Max Memory Used` log line to confirm 1024 MB is enough).
- Validated the driver in-process via Starlette `TestClient` (local app == oracle): **19 checks, 0 mismatches**. Rollback trigger is now "driver reports any mismatch", not a metric threshold.
- `PHASE5_CUTOVER.md` §1–§4 updated accordingly.

### 2026-06-23 — differential driver run vs LIVE legacy test stage: 19/19 match ✅
Ran `drive_live.py` against the **currently-deployed legacy Graphene** model API on the `test` stage (direct execute-api endpoint; URL + key supplied out-of-band, not stored). Identity confirmed: `about` → "Hello, I am nshm_model_graphql_api, version: 0.4.2", root `QueryRoot` with all 6 fields.
- **Result: 19 checks, 0 mismatches** — 3 corpus queries + both model versions × (full tree + a `node(id)` for all 7 Relay types). The new Strawberry oracle is byte-for-byte identical to what AWS serves today.
- **Two risks retired empirically:**
  1. Parity holds not just vs our local legacy, but vs the **live deployment**.
  2. The nzshm-model 0.14→0.15 **data-skew worry is moot** — live data matches the local 0.15.0 oracle exactly, so the version bump is not client-visible. **No need to pin nzshm-model for cutover.**
- Also validated the driver against real infra (URL/x-api-key/network/JSON). Read-only; no changes deployed.
- **Implication:** cutover is low-risk — the contract is proven identical end-to-end *before* touching the deployment. Post-deploy-to-test, expect `drive_live` green again (oracle == deployed-new, same `uv.lock`).
- **Also ran vs PROD** (legacy graphene v0.4.2, stack `nzshm22-model-graphql-api-prod`, AWS acct 461564345538 via `nshm-admin` SSO): **19/19 match** too. Both live stages are byte-identical to the new oracle. Prod endpoint/key obtained via `sls info --stage prod` (key not stored). Same account for test+prod.

### 2026-06-23 — TEST cutover live ✅ (holding before deps/prod)
- Merged the stack **P0–P4 into `deploy-test` as one combined merge** (#67, base retargeted to deploy-test, carrying #63–#66; #63/#67 show MERGED, #64–#66 closed as "landed via #67"). Chose one merge → **one deploy** to avoid pushing a broken intermediate (P1's minimal schema) that could also break the stitched `weka-app-api` test.
- **Deploy run succeeded** (tests + deploy). This is the real, deferred-from-P4 proof that **SF v4's built-in python-requirements packages the deps** without serverless-wsgi; the deploy's built-in `{about}` smoke passed.
- `drive_live.py` vs the **deployed new Strawberry app** on test = **19/19 match** (oracle == deployed-new). The migrated app is live on test and byte-identical to the legacy it replaced.
- **Held per instruction:** #68 (vuln bumps) and #69 (this P5 docs PR) remain open; prod NOT promoted. Remaining test-stage step: the manual weka exercise.

<!-- Append new dated entries above this line as the migration proceeds. -->
