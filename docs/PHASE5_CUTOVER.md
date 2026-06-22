# Phase 5 — Cutover & rollback runbook

Companion to [`MIGRATION_LOG.md`](MIGRATION_LOG.md) and the
[migration runbook](../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md) Phase 5.

**Cutover model: in-place replacement, not parallel.** The Strawberry/Mangum app
deploys to the **same** CloudFormation stack (`nzshm22-model-graphql-api-<stage>`),
same function, same API Gateway routes (`/graphql`, `/graphql/{proxy+}`,
`static/{proxy+}`), same `TempApiKey-*`, same URL. `serverless deploy` updates the
stack in place — the new Lambda overwrites the legacy WSGI/Flask one. There is no
blue/green and no standby. **Therefore rollback = redeploy the previous code.**

Order of operations: deploy to **test** (from `deploy-test`) → corpus + smoke →
soak → promote `deploy-test → main` (deploys **prod**) → watch.

---

## 1. Rollback

### 1a. Test stage (deployed from `deploy-test`)
The test stage redeploys on every push to `deploy-test`. To roll back:

```bash
# Revert the migration on deploy-test and let CI redeploy the legacy app.
git checkout deploy-test && git pull
git revert --no-edit <first-migration-sha>^..<last-migration-sha>   # or revert the squash-merge commit
git push origin deploy-test            # triggers deploy-to-aws.yaml → legacy redeployed
```
Then re-run the smoke replay (§ smoke below) against the test URL to confirm legacy behaviour is restored.

### 1b. Prod (promoted via `deploy-test → main`)
**Pre-staged draft revert PR** — open it as a *draft* immediately after the promote
PR merges (you need the merge SHA), so it's one click to publish under stress:

```bash
# After the promote PR merges to main:
MERGE_SHA=<promote-merge-sha>
git checkout main && git pull
git checkout -b revert/strawberry-promote
git revert --no-edit -m 1 "$MERGE_SHA"     # -m 1 for a merge commit; drop -m for a squash commit
git push -u origin revert/strawberry-promote
gh pr create --base main --head revert/strawberry-promote --draft \
  --title "revert: promote nshm-model-graphql-api to Strawberry" \
  --body "Rollback for <promote-PR-url>. Publish + merge if the trigger below fires. \`git revert ${MERGE_SHA}\`."
```

**Publish + merge the draft when the trigger fires** (see § Trigger). Merging to
`main` redeploys legacy to prod. Then re-run the smoke replay against prod and
**file a follow-up issue with the failure signature before anyone goes to sleep**.

### Trigger criteria (decide the numbers before promote; fill in)
Publish the rollback if **any** of:
- The differential live driver (§2) reports **any mismatch** vs the local oracle (or any HTTP/GraphQL error), **or**
- The manual weka exercise (§3) shows a broken Logic Tree view, **or**
- Any unhandled exception in `aws logs tail /aws/lambda/<fn-name>` within the first 30 min.

> Metric-based triggers (5xx rate, p95 regression) are **not primary here** — traffic
> is too low to produce a meaningful baseline. The differential driver is the signal.

> Forward-port rule (runbook §4.11): any hotfix to `main` MUST be cherry-picked
> back to `deploy-test` the same day, and vice-versa.

---

## 2. Validation — differential live driver (primary)

**Why not a soak:** Model has almost no organic traffic, so a passive soak + CloudWatch
baseline gives no signal. Instead we **actively drive** queries at the deployed `/graphql`
and compare each response **byte-for-byte against the in-process Strawberry schema** (the
oracle, proven identical to legacy — `tests/test_schema_parity.py`). Any difference is
something the *deploy* introduced (packaging, serialization, env, cold-start data load).

```bash
# capture the deployed URL + API key from the deploy run output (the TempApiKey-* line)
uv run python tests/smoke/drive_live.py --url <stage-graphql-url> --api-key <key>
# or: SMOKE_URL=<stage-graphql-url> SMOKE_API_KEY=<key> uv run python tests/smoke/drive_live.py
```

It enumerates (not sampled-from-traffic):
- the no-variable corpus queries (about, root info, get_models),
- **every** model version → the full weka tree query,
- **every** Relay node type, per version → a `node(id)` lookup (ids harvested from the tree).

Exit 0 = every live response matched the oracle. **Any mismatch is the rollback trigger** (§1).
The deploy workflow's built-in one-shot smoke (`query QueryRoot{about}`) still runs first as
a liveness gate; this driver is the correctness gate.

---

## 3. Manual weka exercise + CloudWatch glance (instead of a soak)

The driver (§2) covers the schema exhaustively but synthetically. Pair it with a
**real-client check**: point weka at the deployed API and drive the actual UI.

1. Set weka's `VITE_GRAPHQL_ENDPOINT` (+ `VITE_GRAPHQL_API_KEY`) to the deployed stage
   (test first, prod after promote).
2. Open the **Logic Tree** view; switch model versions; open the **Source Branches** and
   **Ground Motion Branches** tabs. This is exactly `LogicTreePageQuery` against the live API.
3. Eyeball: branch sets/branches render, `gsim_args` shows, no console/network errors.

**CloudWatch is a quick sanity glance, not a baseline/soak** (traffic too low to compare
metrics meaningfully): after the driver + weka runs, confirm `Errors`/`Throttles` ≈ 0 and
check one Lambda `REPORT` log line for `Max Memory Used` < 1024 MB (validates the P1
2048→1024 drop). If memory is tight, bump it back up.

---

## 4. Promote & prod watch

1. Promote `deploy-test → main` via PR (title: `release: promote nshm-model-graphql-api to Strawberry`)
   — only after the driver (§2) + weka exercise (§3) pass on **test**. Requires review from
   someone who didn't write the migration.
2. **Immediately open the draft revert PR** (§1b) with the promote merge SHA.
3. Run the differential driver (§2) against **prod**, then the weka exercise (§3) against prod.
4. **Watch prod ~30 min:** `aws logs tail /aws/lambda/<fn-name> --follow --since 1m` for any
   unhandled exception; quick CloudWatch glance that `Errors`/`Throttles` ≈ 0.
5. **"Healthy" call** once the prod driver run is clean, or **roll back** (§1b) if a trigger fires.
6. After healthy: at cutover, delete the legacy `schema/` package + Flask app + legacy
   deps (`flask`, `flask-cors`, `graphene`, `graphql-server`) and the `legacy` test
   param; rename `strawberry_schema.py` → `schema.py`.

