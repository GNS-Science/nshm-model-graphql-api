# Client query corpus — migration parity

Real-world GraphQL queries replayed against a deployed stage to catch **runtime**
regressions that SDL parity (`schema.legacy.graphql`) misses (runbook Phase 0
step 2 / Phase 3 step 7).

## Status: SEED ONLY

These queries are **derived from the test suite and the deploy smoke query**, not
yet from real production clients. Per the runbook (Trap #1: "New SDL passes parity
check, prod query still breaks"), this corpus must be expanded with **real**
queries from:

- `runzi`
- the web frontends (kororaa / NSHM site)
- any internal scripts using this API

Each file is one query, named `<client>__<purpose>.graphql`. The leading comment
records the calling component. Vendor real query *text* (do not live-fetch at test
time — that introduced a deploy-time dependency in toshi-api, PR #325).

## How it's replayed

A CI job (added in Phase 3) executes each `*.graphql` here against the test-stage
deploy and asserts the response shape matches legacy (modulo `@deprecated` notices).
