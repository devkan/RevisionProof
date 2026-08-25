# RevisionProof handoff

Updated: 2026-08-26

## Current status

The hardened v2 hackathon flow is deployed from tracked source commit `6977747` to the isolated GCP project `revisionproof-agentic-2026-kan`. Cloud Build `354696e9-0fdc-451c-9e69-cf55184ea63f` succeeded, Artifact Registry recorded image digest `sha256:d8b4daad7107428776de4339726ba45fc32f60cee204ddf36a1d443f1cba8dfc`, and Cloud Run revision `revisionproof-staging-00003-q56` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

The service is intentionally and visibly `FIXTURE`. `/health`, `/ready`, and `/api/runtime` report healthy foundation infrastructure while keeping `live_ready=false` and `integration_execution_verified=false`. The latest local gates pass with 56 backend tests, one frontend Vitest regression, Ruff, ESLint, Vite build, and three consecutive real-media rehearsals. gstack then completed the deployed candidate-A path with zero console errors or failed requests: A approval at 1.05x, v2 CTA failure and publish block, repaired v3 with three PASS checks, human Delivery approval, and a 12-event raw trace. See `docs/qa-report-2026-08-26-cloud-deploy.md`.

## Remaining work

ClickHouse Cloud database, roles, secrets, persisted audit rows, and the guarded LIVE deployment remain the next phase. Do not begin it until the user asks; ClickHouse was deliberately deferred. Full restart hydration of an in-progress run is still unimplemented. A GitHub PR or merge has not been requested.

For later operations, run every Cloud Shell command with `CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com`, `CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan`, and the explicit project argument where supported. The latest guarded inventory and cleanup dry-run both exited 0; their Cloud Shell output paths and exact resource set are recorded in `docs/infrastructure-inventory-2026-08-26.md`.

## Watchouts

Never present fixture traces as live. A configured `LIVE` badge is not success evidence; the run must show actual Gemini and `mcp-clickhouse.run_query` events plus persisted target rows. `max-instances=1` prevents cross-instance splits but does not survive a restart. The public FIXTURE create route uses one anonymous instance-global allowance, so one caller can consume the shared 12-runs-per-minute bucket even though spend is bounded. The build service account keeps project-level `roles/run.admin` for bootstrap deployment; consider a conditional or custom role after the hackathon spike. The KRW 30,000 budget is alert-only, not a spending cap. Codex-assisted source may also affect hackathon eligibility; the user plans a separate Gemini review/rework before submission.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `6977747`
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; implementation commit `6977747` is pushed. See `git log` for the deployment documentation checkpoint. No PR or merge has been performed.

## Start here

Read `docs/README.md`, the 2026-08-26 QA report, and the 2026-08-26 infrastructure delta. Use `docs/demo-runbook.md` for the judge path. The next engineering gate is credential-backed LIVE verification, not more fixture polish.
