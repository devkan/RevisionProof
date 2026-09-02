# RevisionProof handoff

Updated: 2026-09-02

## Current status

The isolated GCP project `revisionproof-agentic-2026-kan` now serves the tracked LIVE implementation from commit `6012e9f`. Cloud Build `c0c3c928-fd5a-47a3-9b04-14ec5fbcbc20` succeeded, the pushed RevisionProof image digest is `sha256:d434e6fbe4e5d9e5be2ea47af590aaf4ffec5cc868cce36238db59d64458aef7`, and Cloud Run revision `revisionproof-staging-00014-r4l` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

The primary product flow now completes the actual edit: Gemini separates executable, clarification-required, and editor-required requests; the user checks a safe request; RevisionProof renders A/B previews; choosing an option generates the full source video; and deterministic verification runs automatically. External MP4 upload remains only as an optional collapsed path for videos edited elsewhere. The redesigned UI uses larger typography, explicit step/status copy, large source/A/B/final viewers, and sticky processing spinners.

LIVE run `01M1H4MDB7NQBDFQF1YNNFM0EB` selected the supported six-second punch-in, anchored it through the official ClickHouse MCP, chose Option B, generated a 30.016-second 1280x720 MP4, and reached `READY` with all three checks PASS. The private object is `runs/01M1H4MDB7NQBDFQF1YNNFM0EB/versions/approved-b.mp4`, generation `1788355551327949`, 817,180 bytes. Source, A/B, final enlarged playback, and browser console state passed LIVE QA. Delivery approval was intentionally not granted.

The LIVE source is now a visually inspectable four-scene storyboard under asset `01M00000000000000000000000`. The default supported note explicitly requests a 6-second punch-in, matching the 4-8 second safety contract. Browser run `01M1GVQRHVVZ1TAQRWJZ1H0ACC` completed Gemini interpretation, official ClickHouse MCP retrieval, A/B rendering, candidate B approval, private GCS upload, and deterministic verification. It reached `READY` with all three checks PASS; delivery approval was intentionally not granted.

The original source and both A/B candidate cards now expose `View larger` controls backed by a shared 960px modal. The viewer is viewport-bounded and supports close-button, Escape, and backdrop dismissal. LIVE run `01M1GY19CVZZ7QDPG5DPPVBAG9` verified source and Option B playback after real Gemini/MCP execution and A/B rendering with no browser console errors.

On 2026-09-02 the user observed a LIVE run fail after Gemini parsing and about 64 seconds of ClickHouse evidence lookup. The reader's hard-coded two 30-second attempts were too short for the sleeping service. `REVISIONPROOF_MCP_MAX_ATTEMPTS` now defaults to three bounded fresh-process attempts. Post-deploy gstack run `01M1GN7EY252SSM5F2AM170TKY` logged `ClickHouse MCP timeout on attempt 1/3`, recovered on the next process, and reached `EVIDENCE_ANCHORED` in a 51.878-second HTTP 201 response with `error=null`. See `docs/qa-report-2026-09-02-mcp-recovery.md`.

Final gstack run `01M0Z3338TYVHWHK4FZRGADTKZ` exercised real `google.vertex.gemini`, real `mcp-clickhouse.run_query`, candidate B (1.12x), blocked v2, repaired v3, private GCS persistence, and ClickHouse persistence. Raw JSON is `READY` with spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5` and `delivery_approved=true`. Event 14 records `Human approved the verified version for delivery` at `2026-08-26T13:48:30.750541Z`. ClickHouse contains one spec, 24 feature rows, and six check rows for the run.

## Remaining work

Submission copy, a 2:45 recording script, and explicit release gates are in `docs/submission-pack-2026-08-27.md` and `docs/demo-recording-script-2026-08-27.md`. Update the recording script to demonstrate request classification, checkbox selection, automatic full-video generation, and the final human delivery gate. The latest full-video QA run reached `READY` but did not grant a new delivery approval.

Before submission: resolve development-tool eligibility with the organizer, obtain owner approval for public repository/video publication and branch landing, perform a clean-clone check and a fresh operator-led LIVE recording, and submit only after owner review. GitHub is currently PRIVATE with default branch `main`; work remains on `review/qa-hardening`. The existing Apache 2.0 notice was completed with the official license body on this branch; GitHub default-branch detection previously reported `Other` and must be rechecked after landing. No PR or merge has been requested.

Full restart hydration remains unimplemented, and the frontend does not restore an active run after refresh. The generated demo is a stylized storyboard plus a synthetic tone, with authored transcript-like seed metadata; it is not transcribed presenter footage. Capture v2's blocked state before v3 replaces the current proof and prunes old local evidence. The existing approved run is historical evidence only, not approval for a new recording run.

For later Cloud Shell operations, select and verify the exact account and project before every mutation: `gcloud config set account secureis@gmail.com`, `gcloud config set project revisionproof-agentic-2026-kan`, then `gcloud config get-value account` and `gcloud config get-value project`. Keep explicit `--project=revisionproof-agentic-2026-kan` flags. Do not use `CLOUDSDK_CORE_ACCOUNT`; the guarded scripts intentionally reject delegated environment overrides. Cloud Shell token refresh may occasionally fail with `metadata server ... missing 'email' field`; stop and reauthorize the existing secureis session rather than switching identities or projects.

## Watchouts

The `LIVE` badge alone is not success evidence; require actual Gemini/MCP events plus persisted target rows. The official MCP reader now retries three fresh processes by default, but a sustained outage still fails closed after the configured limit. Cloud Run uses concurrency 4, min/max 1: four slots prevent the long-lived SSE stream from starving mutations, while one instance preserves the current process-local repository boundary. A restart still requires a new run. Do not drop ClickHouse backup table `revisionproof.segments_pre_seed_dedupe_20260826`. The bootstrap admin is deleted; durable view definer `revisionproof_view_definer_user` must remain. The KRW 30,000 budget is alert-only, not a hard cap. Codex-assisted source may affect hackathon eligibility; the user plans a separate Gemini review/rework before submission, but that alone does not establish eligibility. Runtime delivery approval does not publish or transmit the video externally.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `6012e9f`
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; deployed implementation commit `6012e9f` is pushed. The documentation checkpoint follows this handoff update. No PR or merge has been performed.

## Start here

Read `docs/README.md`, `docs/qa-report-2026-09-02-automatic-full-video-ui.md`, `docs/submission-pack-2026-08-27.md`, and `docs/demo-recording-script-2026-08-27.md`. Use `docs/qa-report-2026-08-26-live-final.md` plus the infrastructure inventory for the full historical delivery-approved proof. The final delivery approval has been performed for the recorded historical run only.
