# RevisionProof handoff

Updated: 2026-08-25

## Current status

The v2 hackathon flow is hardened on local branch `review/qa-hardening`. Three feedback safety classes are enforced, unsupported notes cannot render, approval freezes the exact ROI/ranges/thresholds in a hash-validated `RevisionSpec`, v2 blocks real delivery approval with CTA before/after evidence, and v3 enables a separate human Delivery approval. Mutations use bounded idempotency keys, version-upload keys are bound to the actual file SHA-256, offline rehearsal is read-only, SSE events carry resumable IDs, candidate uploads are not publicly served, and the container is configured for a non-root user.

Verified baseline: 36 backend tests, Ruff, ESLint, Vite build, the 12-video zero-false-PASS corpus, and three consecutive 12-event real-media rehearsals all pass. gstack browser QA completed the full desktop path, the 375px classification and v2 blocked paths, offline read-only mode, and the SHA-256-bound version upload with zero application console errors. One mobile input-height issue was fixed and reverified. See `docs/qa-report-2026-08-25-v2-hardening.md`.

## Remaining work

Provision or attach the target GCP project, Vertex/ADK credentials, private GCS bucket with 24-hour lifecycle, ClickHouse Cloud database and roles, and Secret Manager values. Then run the live integration spike, rebuild the Docker image with Docker Desktop running, rehearse LIVE three times, and deploy only after explicit authorization. Full restart hydration of an in-progress run remains unimplemented.

## Watchouts

Never present fixture traces as live. A configured `LIVE` badge is not success evidence; the run must show actual Gemini and `mcp-clickhouse.run_query` events and persisted rows. `max-instances=1` prevents in-memory state from splitting across instances but does not survive a restart. Docker rebuild for this hardening branch was blocked because the daemon was stopped. Codex-assisted source may also affect hackathon eligibility; the user plans a separate Gemini review/rework before submission.

## Git state

- Branch: `review/qa-hardening`
- Implementation commits: `d7dd18e`, `a9ce687`, `3c422bc`; see `git log` for the final docs checkpoint
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push/PR/deploy: not performed

## Start here

Read `docs/README.md`, then run the quality gates in `README.md` and the judge path in `docs/demo-runbook.md`. The next engineering gate is credential-backed LIVE verification, not more fixture polish.
