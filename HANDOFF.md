# RevisionProof handoff

Updated: 2026-08-26

## Current status

The isolated GCP project `revisionproof-agentic-2026-kan` now serves the tracked LIVE implementation from commit `d1b9a10`. Cloud Build `d5845e1e-9123-4e81-81cb-0fb3f6b607ec` succeeded, the pushed RevisionProof image digest is `sha256:54e2427d56e8408dfd712c4864df8dec555d127f4b1380a070bbfe2b662e73e3`, and Cloud Run revision `revisionproof-staging-00009-mbh` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

Final gstack run `01M0Z3338TYVHWHK4FZRGADTKZ` exercised real `google.vertex.gemini`, real `mcp-clickhouse.run_query`, candidate B (1.12x), blocked v2, repaired v3, private GCS persistence, and ClickHouse persistence. Raw JSON ended in `READY` with spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5` and `delivery_approved=false`. ClickHouse contains one spec, 24 feature rows, and six check rows for the run.

## Remaining work

Full restart hydration of an in-progress run remains unimplemented. Before a submission recording, rehearse the LIVE judge path and decide explicitly whether the final run should receive the separate delivery approval. No PR or merge has been requested.

For later Cloud Shell operations, select and verify the exact account and project before every mutation: `gcloud config set account secureis@gmail.com`, `gcloud config set project revisionproof-agentic-2026-kan`, then `gcloud config get-value account` and `gcloud config get-value project`. Keep explicit `--project=revisionproof-agentic-2026-kan` flags. Do not use `CLOUDSDK_CORE_ACCOUNT`; the guarded scripts intentionally reject delegated environment overrides. Cloud Shell token refresh may occasionally fail with `metadata server ... missing 'email' field`; stop and reauthorize the existing secureis session rather than switching identities or projects.

## Watchouts

The `LIVE` badge alone is not success evidence; require actual Gemini/MCP events plus persisted target rows. Cloud Run uses concurrency 4, min/max 1: four slots prevent the long-lived SSE stream from starving mutations, while one instance preserves the current process-local repository boundary. A restart still requires a new run. Do not drop ClickHouse backup table `revisionproof.segments_pre_seed_dedupe_20260826`. The bootstrap admin is deleted; durable view definer `revisionproof_view_definer_user` must remain. The KRW 30,000 budget is alert-only, not a hard cap. Codex-assisted source may affect hackathon eligibility; the user plans a separate Gemini review/rework before submission.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `d1b9a10`
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; the implementation commit is pushed. The final documentation/QA checkpoint follows this handoff update. No PR or merge has been performed.

## Start here

Read `docs/README.md`, `docs/qa-report-2026-08-26-live-final.md`, and the 2026-08-26 infrastructure inventory. Use `docs/demo-runbook.md` for the judge path. The next product decision is whether to execute the separate final delivery approval; it has not been performed.
