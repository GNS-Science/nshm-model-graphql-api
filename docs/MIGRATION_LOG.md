# Graphene → Strawberry Migration Log — `nshm-model-graphql-api`

**This API is the pilot migration** for the Graphene 3 / Flask / serverless-wsgi → Strawberry / FastAPI / Mangum effort across the four GraphQL siblings.

**Authoritative runbook:** [`../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md`](../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md)
(reference migration: `nshm-toshi-api`, completed 2026-06). Read it first — this log only records **what is specific to this repo** and **what actually happened** here. Per the runbook's "Maintenance" rule, every surprise found here must be folded back into that runbook (one-line note or new trap), and this API MUST file at least one PR against it.

- **Owner:** Chris B Chamberlain (chrisbc@artisan.co.nz)
- **Migration branch:** `migrate/strawberry` (based on `deploy-test`)
- **Started:** 2026-06-22
- **Status:** Phase 1 — Bootstrap ✅ complete (2026-06-22); next: Phase 2 schema migration
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
| Remove `pull_request.branches:` filter (Trap #14) | ✅ Yes | present in `dev.yml` |
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

### Phase 2 — Schema migration (the 7 types)
- [ ] `NshmModel` + root `Query` (`get_models`, `get_model`, `about`, `version`, `current_model_version`, `node`)
- [ ] Source tree: `SourceLogicTree` → `SourceBranchSet` → `SourceLogicTreeBranch` + `BranchSource` union
- [ ] GMM tree: `GroundMotionModelLogicTree` → `GmmBranchSet` → `GmmLogicTreeBranch`
- [ ] Relay `Node` via `strawberry.relay`; preserve every composite-ID delimiter scheme above
- [ ] `gsim_args` JSON scalar parity; `strawberry.lazy` for any forward refs

### Phase 3 — Tests
- [ ] Port `graphene.test.Client` → Strawberry test client (add `conftest.py` with a shared fixture)
- [ ] SDL parity CI check vs `schema.legacy.graphql`
- [ ] Query-corpus replay job

### Phase 4 — Deploy / CI / deps
- [ ] Remove `branches:` filter in `dev.yml` (Trap #14)
- [ ] Memory sizing watch (1024 MB → adjust on CloudWatch)
- [ ] Address Dependabot vulns; `uv sync --frozen` in CI
- [ ] Confirm API-Gateway key auth unchanged; `/graphql` path preserved

### Phase 5 — Cutover
- [ ] Deploy to `test` stage from `deploy-test`; run corpus + smoke (`{about}`)
- [ ] Pre-stage rollback PR; promote `deploy-test → main`; watch prod 30 min

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

<!-- Append new dated entries above this line as the migration proceeds. -->
