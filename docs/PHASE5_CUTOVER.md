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
