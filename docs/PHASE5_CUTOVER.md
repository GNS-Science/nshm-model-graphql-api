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
- Smoke replay (§2) fails on the deployed stage (any corpus query errors / shape mismatch), **or**
- Prod **5xx rate > `__%` sustained > `__ min`** (CloudWatch `5XXError`), **or**
- p95 `Duration` regresses **> `__×`** vs the pre-deploy baseline (capture it — runbook Trap #22), **or**
- Any unhandled exception in `aws logs tail /aws/lambda/<fn-name>` within the first 30 min that affects real client queries.

> Forward-port rule (runbook §4.11): any hotfix to `main` MUST be cherry-picked
> back to `deploy-test` the same day, and vice-versa.

---

## 2. Smoke

The deploy workflow already runs a one-shot smoke query (`query QueryRoot{about}`).
For real coverage, replay the **whole vendored corpus** against the deployed stage —
this is the runtime check that SDL parity can't give (runbook Trap #1):

```bash
# capture the deployed URL + API key from the deploy run output (the TempApiKey-* line)
uv run python tests/smoke/replay_corpus.py --url <stage-graphql-url> --api-key <key>
# or: SMOKE_URL=... SMOKE_API_KEY=... uv run python tests/smoke/replay_corpus.py
```
Every query (incl. the real weka `LogicTreePageQuery`) must return HTTP 200 with no
GraphQL `errors`. This is the **rollback trigger** referenced in §1: any failure here
on prod → publish the draft revert PR.

---

## 3. Soak

1. **Baseline first (before deploying).** Screenshot the legacy Lambda's CloudWatch
   `Duration` p50/p95/p99, `5XXError` rate, `Invocations`, and `Memory Utilization`
   over a representative window — this is "healthy" for comparison (runbook Trap #22).
   Memory matters here: we dropped 2048 → **1024 MB** (P1); confirm utilization leaves
   headroom or bump back up.
2. **Deploy to test** (push to `deploy-test`), then run the smoke replay (§2).
3. **Soak the test stage.** Runbook default is 24h; **Model is the explicit
   skip-candidate** (very low real traffic). Recommended here: a short soak
   (a few hours, or until the next real client hit) rather than a full 24h — call it
   based on observed traffic. Re-run the corpus replay at the end of the soak.
4. **Watch during soak:** CloudWatch `Duration` (p95 vs baseline), `5XXError`,
   `Invocations`, `Memory Utilization` (for the 1024 MB call), and
   `aws logs tail /aws/lambda/<fn-name> --follow` for unhandled exceptions.

---

## 4. Promote & prod watch

1. Promote `deploy-test → main` via PR (title: `release: promote nshm-model-graphql-api to Strawberry`)
   — only after corpus + smoke + soak pass. Requires review from someone who didn't write the migration.
2. **Immediately open the draft revert PR** (§1b) with the promote merge SHA.
3. **Watch prod ≥ 30 min**, two windows side by side:
   - `aws logs tail /aws/lambda/<fn-name> --follow --since 1m` — any unhandled exception / 5xx
   - CloudWatch graph: `Invocations`, `5XXError`, p95 `Duration` vs the §3 baseline
4. Run the smoke replay (§2) against **prod**.
5. **"Healthy" call** at 30 min, or **roll back** (§1b) if a trigger fires.
6. After healthy: at cutover, delete the legacy `schema/` package + Flask app + legacy
   deps (`flask`, `flask-cors`, `graphene`, `graphql-server`) and the `legacy` test
   param; rename `strawberry_schema.py` → `schema.py`.

