# RevisionProof handoff

Updated: 2026-08-25

## Current status

The v2 hackathon vertical slice is implemented from a clean repository: fixture feedback interpretation, evidence anchoring, real FFmpeg A/B previews, immutable human-approved spec, actual OpenCV/FFmpeg regression verification, a v2 blocked result, and a v3 ready result. React/Vite is served by FastAPI from one container.

Verified baseline: 28 backend tests pass, the 12-video regression corpus produces 3 expected passes and 9 expected failures with zero false PASS results, three consecutive rehearsals finish READY, the Docker image serves healthy probes and the SPA, and ClickHouse 25.6 enforces separate view-only reader and insert-only writer roles. gstack browser QA completed the desktop path and the 375px mobile layout with zero console errors or undersized interactive controls.

## Remaining work

Configure the target GCP project, ClickHouse Cloud instance, GCS bucket, service accounts, and Secret Manager values; then run the live integration spike and update `docs/integration-status.md` with observed evidence. Deployment has not been authorized or performed.

## Watchouts

Never present fixture traces as live. The deterministic verifier, not Gemini, owns release verdicts. Re-run three rehearsals after media, threshold, or state-machine changes. The all-integrations image is 1,444,809,562 bytes because Google ADK/MCP/OpenCV and Debian FFmpeg are shipped together; keep it for the hackathon, but measure Cloud Run cold starts before production.

## Start here

Read `docs/README.md`, then run the quality gates in `README.md` and the judge path in `docs/demo-runbook.md`.
