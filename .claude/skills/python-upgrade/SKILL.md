---
name: python-upgrade
description: Audit and upgrade Python dependencies to fix vulnerabilities and apply patch-level updates, with test verification.
allowed-tools: Bash, Read, Edit, Write, Agent, WebFetch, WebSearch
user-invocable: true
---

Our Python dependencies have vulnerabilities that we want to fix by upgrading.

## Setup

Switch to git branch "chore/upgrade", creating it if it doesn't exist.
Start with `poetry sync --with dev` to be up to date with the lock file.

## Auditing

- Run `poetry run pip-audit` to list vulnerabilities.
- Run `poetry show --outdated` to see packages that can be upgraded in general.

## Upgrading

- Use `poetry update <package-name>` to upgrade a dependency within the version range in pyproject.toml.
- Use `poetry add <package>` to upgrade a package to something outside the version range in pyproject.toml.
- Avoid code changes unless the fix is trivial (e.g., an import path change). If code changes are needed, note them in the summary.
- Transitive dependencies can be upgraded if they have a security vulnerability. Note any upgraded transitive dependencies in the summary.
- Ask before upgrading pinned versions.

## Severity lookup

Severity information for each vulnerability can be found like so https://github.com/advisories?query=CVE-2025-14009. Look up each advisory to determine its severity (critical, high, medium, low).

## Upgrade strategy

1. Run `pip-audit` and collect all vulnerabilities.
2. Look up the severity of each vulnerability.
3. Display a plan as a table showing each vulnerability with: package name, current version, fixed version, advisory ID, severity, depndency group (for exmaple "dev"), and the semantic version increase required.
4. Sort the plan by: severity (critical first), then by smallest semantic version increase first.
5. Perform all upgrades in the plan.
6. Run `poetry run pytest` to see if the upgrades were successful.
7. If all tests passed, perform all other outstanding upgrades if they are at patch level and within pyproject.toml ranges.
8. Run `poetry run pytest` to see if all upgrades were successful.
9. If any upgrade fails or if any test fails, roll back all changes with `git checkout -- poetry.lock pyproject.toml && poetry sync --with dev` and use the "Careful Upgrade Strategy".

## Careful Upgrade Strategy

1. Use this strategy if the general upgrade strategy fails.
2. Use the plan created by the general upgrade strategy.
3. Upgrade dependencies **one by one**, running `poetry run pytest` after each upgrade to ensure everything still works.
4. If a test fails after an upgrade, revert that upgrade and move on to the next one. Note which upgrades were skipped and why.
5. It might not be possible to upgrade all dependencies. Use your best effort.

Think hard about dependency interactions and potential breaking changes.

## Integration test

After all achievable upgrades are complete, run a final integration test by starting the local server and sending a test GraphQL query:

1. Run `yarn install` if node_modules are not present.
2. Temporarily change `pythonBin: python3` to `pythonBin: python` in `serverless.yml` (needed for Windows compatibility).
3. Start the server in the background, wait for it to be ready, then send a query:

```bash
ENABLE_METRICS=0 poetry run yarn sls wsgi serve > /tmp/server.log 2>&1 &
SERVER_PID=$!
```

Then in a separate command, poll the log file until the server is ready before sending the query. The server is ready when the log contains "Serving on". Retry up to 10 times with 3-second sleeps:

```bash
for i in $(seq 1 10); do
  if grep -q "Serving on" /tmp/server.log 2>/dev/null; then
    echo "Server is ready"
    break
  fi
  echo "Waiting for server... (attempt $i)"
  sleep 3
done

cat /tmp/server.log

curl -s -X POST http://localhost:5000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ version about get_models { version } }"}' 2>&1
```

If the server log does not contain "Serving on" after all retries, print the log contents and report the failure instead of sending the query.

Then clean up:

```bash
kill $SERVER_PID 2>/dev/null
```

4. Verify the response contains valid `version`, `about`, and `get_models` data.
5. Revert the `pythonBin` change in `serverless.yml` back to `python3`.

## Bump version

When done, create a commit and bump the version with

```bash
poetry run bump2version patch
```
