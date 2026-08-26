# RevisionProof handoff

Updated: 2026-08-26

## Current status

The hardened v2 FIXTURE flow remains deployed from tracked source commit `6977747` to the isolated GCP project `revisionproof-agentic-2026-kan`. Cloud Build `354696e9-0fdc-451c-9e69-cf55184ea63f` succeeded, Artifact Registry recorded image digest `sha256:d8b4daad7107428776de4339726ba45fc32f60cee204ddf36a1d443f1cba8dfc`, and Cloud Run revision `revisionproof-staging-00003-q56` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

The service is intentionally and visibly `FIXTURE`. Uncommitted LIVE hardening now passes 86 backend tests, two frontend tests, Ruff, ESLint, Vite, Dockerized ShellCheck, and a fresh ClickHouse 25.6 integration job. Vertex credential probes passed in `global`, GCP IAM was reduced to bucket-scoped create/view access plus a 16-permission Cloud Run deployer role, and cleanup now records the custom role. These facts do not make the deployed revision LIVE. See `docs/live-hardening-progress-2026-08-26.md`.

## Remaining work

The ClickHouse Cloud tab remains at sign-in. After the user signs in with the intended `secureis` identity, create a dedicated RevisionProof service, record its exact host, create the two numeric-version secrets, run the guarded bootstrap, and deploy only after the official MCP anchor smoke test passes. Full restart hydration of an in-progress run is still unimplemented. A GitHub PR or merge has not been requested.

For later operations, run every Cloud Shell command with `CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com`, `CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan`, and the explicit project argument where supported. The latest guarded inventory and cleanup dry-run both exited 0; their Cloud Shell output paths and exact resource set are recorded in `docs/infrastructure-inventory-2026-08-26.md`.

## Watchouts

Never present fixture traces as live. A configured `LIVE` badge is not success evidence; the run must show actual Gemini and `mcp-clickhouse.run_query` events plus persisted target rows. `max-instances=1` and concurrency 1 do not survive a restart. The KRW 30,000 budget is alert-only, not a spending cap. The GCP custom deployer role is narrower than `roles/run.admin`, but the source configuration has not yet been exercised by a new Cloud Build. Codex-assisted source may also affect hackathon eligibility; the user plans a separate Gemini review/rework before submission.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `6977747`; current source HEAD: `551447f` plus reviewed uncommitted LIVE hardening
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; implementation commit `6977747` is pushed. See `git log` for the deployment documentation checkpoint. No PR or merge has been performed.

## Start here

Read `docs/README.md`, the 2026-08-26 QA report, and the 2026-08-26 infrastructure delta. Use `docs/demo-runbook.md` for the judge path. The next engineering gate is credential-backed LIVE verification, not more fixture polish.
