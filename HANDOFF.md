# RevisionProof handoff

Updated: 2026-08-25

## Current status

The v2 hackathon flow is hardened on local branch `review/qa-hardening`. Three feedback safety classes are enforced, unsupported notes cannot render, approval freezes the exact ROI/ranges/thresholds in a hash-validated `RevisionSpec`, v2 blocks real delivery approval with CTA before/after evidence, and v3 enables a separate human Delivery approval. Mutations use bounded idempotency keys, version-upload keys are bound to the actual file SHA-256, offline rehearsal is read-only, SSE events carry resumable IDs, candidate uploads are not publicly served, and the container is configured for a non-root user.

Verified baseline: 36 backend tests, Ruff, ESLint, Vite build, the 12-video zero-false-PASS corpus, and three consecutive 12-event real-media rehearsals all pass. gstack browser QA completed the full desktop path, the 375px classification and v2 blocked paths, offline read-only mode, and the SHA-256-bound version upload with zero application console errors. One mobile input-height issue was fixed and reverified. See `docs/qa-report-2026-08-25-v2-hardening.md`.

## Remaining work

Complete `gcloud auth login secureis@gmail.com` inside Cloud Shell, then run the idempotent foundation inventory and submit Cloud Build for the visibly labeled FIXTURE staging service. The isolated project `revisionproof-agentic-2026-kan` (number `348672234012`) is linked to billing account `0134C0-F341A5-D149BA`; APIs, least-privilege IAM, Artifact Registry, private GCS, and the KRW 30,000 project budget are already console-created and verified. ClickHouse Cloud database/roles/secrets and the guarded LIVE deployment remain the following phase. Full restart hydration of an in-progress run remains unimplemented.

## Watchouts

Never present fixture traces as live. A configured `LIVE` badge is not success evidence; the run must show actual Gemini and `mcp-clickhouse.run_query` events and persisted rows. `max-instances=1` prevents in-memory state from splitting across instances but does not survive a restart. Docker Desktop now runs and both the full and foundation images passed non-root local health checks; see `docs/infrastructure-inventory-2026-08-25.md`. GCP control-plane resources exist, but no image/build/Cloud Run revision exists until Cloud Shell CLI OAuth is completed directly by the user. The KRW 30,000 budget is alert-only, not a spending cap. Codex-assisted source may also affect hackathon eligibility; the user plans a separate Gemini review/rework before submission.

## Git state

- Branch: `review/qa-hardening`
- Implementation commits: `d7dd18e`, `a9ce687`, `3c422bc`; see `git log` for the final docs checkpoint
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; GCP foundation checkpoints through `fdfd266` were pushed. PR and Cloud Run deploy are not yet performed.

## Start here

Read `docs/README.md`, then run the quality gates in `README.md` and the judge path in `docs/demo-runbook.md`. The next engineering gate is credential-backed LIVE verification, not more fixture polish.
