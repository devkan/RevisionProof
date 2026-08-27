# RevisionProof handoff

Updated: 2026-08-27

## Current status

The isolated GCP project `revisionproof-agentic-2026-kan` now serves the tracked LIVE implementation from commit `d1b9a10`. Cloud Build `d5845e1e-9123-4e81-81cb-0fb3f6b607ec` succeeded, the pushed RevisionProof image digest is `sha256:54e2427d56e8408dfd712c4864df8dec555d127f4b1380a070bbfe2b662e73e3`, and Cloud Run revision `revisionproof-staging-00009-mbh` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

Final gstack run `01M0Z3338TYVHWHK4FZRGADTKZ` exercised real `google.vertex.gemini`, real `mcp-clickhouse.run_query`, candidate B (1.12x), blocked v2, repaired v3, private GCS persistence, and ClickHouse persistence. Raw JSON is `READY` with spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5` and `delivery_approved=true`. Event 14 records `Human approved the verified version for delivery` at `2026-08-26T13:48:30.750541Z`. ClickHouse contains one spec, 24 feature rows, and six check rows for the run.

## Remaining work

Submission copy, a 2:45 recording script, and explicit release gates are now in `docs/submission-pack-2026-08-27.md` and `docs/demo-recording-script-2026-08-27.md`. A read-only gstack smoke on 2026-08-27 confirmed healthy LIVE responses and the unchanged approved run. No new LIVE execution, reapproval, or deployment was performed.

Before submission: resolve development-tool eligibility with the organizer, obtain owner approval for public repository/video publication and branch landing, perform a clean-clone check and a fresh operator-led LIVE recording, and submit only after owner review. GitHub is currently PRIVATE with default branch `main`; work remains on `review/qa-hardening`. The existing Apache 2.0 notice was completed with the official license body on this branch; GitHub default-branch detection previously reported `Other` and must be rechecked after landing. No PR or merge has been requested.

Full restart hydration remains unimplemented, and the frontend does not restore an active run after refresh. The generated demo is geometric video plus a synthetic tone, with authored transcript-like seed metadata; it is not transcribed presenter footage. Capture v2's blocked state before v3 replaces the current proof and prunes old local evidence. The existing approved run is historical evidence only, not approval for a new recording run.

For later Cloud Shell operations, select and verify the exact account and project before every mutation: `gcloud config set account secureis@gmail.com`, `gcloud config set project revisionproof-agentic-2026-kan`, then `gcloud config get-value account` and `gcloud config get-value project`. Keep explicit `--project=revisionproof-agentic-2026-kan` flags. Do not use `CLOUDSDK_CORE_ACCOUNT`; the guarded scripts intentionally reject delegated environment overrides. Cloud Shell token refresh may occasionally fail with `metadata server ... missing 'email' field`; stop and reauthorize the existing secureis session rather than switching identities or projects.

## Watchouts

The `LIVE` badge alone is not success evidence; require actual Gemini/MCP events plus persisted target rows. Cloud Run uses concurrency 4, min/max 1: four slots prevent the long-lived SSE stream from starving mutations, while one instance preserves the current process-local repository boundary. A restart still requires a new run. Do not drop ClickHouse backup table `revisionproof.segments_pre_seed_dedupe_20260826`. The bootstrap admin is deleted; durable view definer `revisionproof_view_definer_user` must remain. The KRW 30,000 budget is alert-only, not a hard cap. Codex-assisted source may affect hackathon eligibility; the user plans a separate Gemini review/rework before submission, but that alone does not establish eligibility. Runtime delivery approval does not publish or transmit the video externally.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `d1b9a10`
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; the deployed implementation and final-approval checkpoint `75a71af` are pushed. The submission-document/license checkpoint follows this handoff update. No PR or merge has been performed.

## Start here

Read `docs/README.md`, `docs/submission-pack-2026-08-27.md`, and `docs/demo-recording-script-2026-08-27.md` for submission preparation. Use `docs/qa-report-2026-08-27-submission-smoke.md` for the latest read-only check, and `docs/qa-report-2026-08-26-live-final.md` plus the 2026-08-26 infrastructure inventory for the full historical LIVE proof. The final delivery approval has been performed for the recorded final run only.
