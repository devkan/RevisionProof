# RevisionProof handoff

Updated: 2026-09-03

## Current status

The ClickHouse intelligence extension is implemented and locally verified: sampled Revision Change Map with enlarged synchronized comparison, Approved Edit Memory with explicit final-approval/private-key save gates, actual EXPLAIN-verified HNSW and QBit alternatives, and checksummed export/restore. Backend 278 tests and frontend 16 tests pass. Real isolated ClickHouse 26.2.19.43 verified HNSW/QBit and duplicate-safe aggregation; a second server verified backup restoration. Docker image `revisionproof:intelligence-20260903` is running in FIXTURE at `http://127.0.0.1:18125`, container `revisionproof-intelligence-demo-20260903`. Linux run `01M1JMQCHKK01N4DJGTVKGJPWX` reached READY with 3 PASS checks and a 30-window map, without delivery approval.

**GitHub push, Cloud migration, deployment and fresh LIVE QA are complete.** The owner requested push/deployment after the scoped grant confirmation. The signed-in ClickHouse console confirmed 26.2.1.641 and the exact project/host sentinel, applied seven new objects and only their necessary grants, and verified all 19 objects including the 12 preserved originals. Commits `c982637` (backend/infrastructure) and `c5652b1` (UI) are pushed to `review/qa-hardening`. Public LIVE Approved Edit Memory is intentionally read-only; its empty library did not execute a vector search. HNSW/QBit execution was verified separately against the populated isolated test server, not claimed for the empty Cloud library. Start with `docs/deployment-2026-09-03-clickhouse-intelligence.md` for current release evidence, then the QA report and runbook. No billing settings, old grants, other projects or backups were changed. No PR, merge or visibility change was made. Two isolated DB test containers remain stopped with volumes retained; the former native dev servers on ports 8000/5173 were stopped.

### Current deployed Cloud release

The isolated GCP project `revisionproof-agentic-2026-kan` serves implementation commit `c5652b1`. Cloud Build `85ae9052-5b5b-43aa-a2bd-5c3004e913ee` succeeded at `2026-09-03T04:17:06.740874Z`, image digest `sha256:3f437dc970c8de36c3c3542160d334de73122ca7d905cd6035b0f6ac74f13459`, and revision `revisionproof-staging-00015-h6b` receives 100% of traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. Health, readiness and runtime endpoints returned 200 with LIVE ready and intelligence enabled. Previous revision `revisionproof-staging-00014-r4l` (source `6012e9f`) remains the rollback target.

Fresh LIVE run `01M1JQSKYVTS5EFNJ6KBEYACHS` used Gemini and the official ClickHouse MCP, generated Option B, and reached `READY` with three PASS checks. Change Map analysis `01M1JQXREQ5MXBXMN5R7P8D498` persisted 60 sampled frame pairs and 30 one-second windows, with six requested-change seconds and zero sampled review flags. ClickHouse independently confirmed one spec and three version-check rows. Private GCS media generation is `1788409203060962`, 817,180 bytes. Desktop/mobile synchronized comparison, playback, seeking, loading spinners, Escape and focus restoration passed browser QA. Delivery approval remains false.

### Earlier releases and historical evidence

The primary product flow now completes the actual edit: Gemini separates executable, clarification-required, and editor-required requests; the user checks a safe request; RevisionProof renders A/B previews; choosing an option generates the full source video; and deterministic verification runs automatically. External MP4 upload remains only as an optional collapsed path for videos edited elsewhere. The redesigned UI uses larger typography, explicit step/status copy, large source/A/B/final viewers, and sticky processing spinners.

LIVE run `01M1H4MDB7NQBDFQF1YNNFM0EB` selected the supported six-second punch-in, anchored it through the official ClickHouse MCP, chose Option B, generated a 30.016-second 1280x720 MP4, and reached `READY` with all three checks PASS. The private object is `runs/01M1H4MDB7NQBDFQF1YNNFM0EB/versions/approved-b.mp4`, generation `1788355551327949`, 817,180 bytes. Source, A/B, final enlarged playback, and browser console state passed LIVE QA. Delivery approval was intentionally not granted.

The LIVE source is now a visually inspectable four-scene storyboard under asset `01M00000000000000000000000`. The default supported note explicitly requests a 6-second punch-in, matching the 4-8 second safety contract. Browser run `01M1GVQRHVVZ1TAQRWJZ1H0ACC` completed Gemini interpretation, official ClickHouse MCP retrieval, A/B rendering, candidate B approval, private GCS upload, and deterministic verification. It reached `READY` with all three checks PASS; delivery approval was intentionally not granted.

The original source and both A/B candidate cards now expose `View larger` controls backed by a shared 960px modal. The viewer is viewport-bounded and supports close-button, Escape, and backdrop dismissal. LIVE run `01M1GY19CVZZ7QDPG5DPPVBAG9` verified source and Option B playback after real Gemini/MCP execution and A/B rendering with no browser console errors.

On 2026-09-02 the user observed a LIVE run fail after Gemini parsing and about 64 seconds of ClickHouse evidence lookup. The reader's hard-coded two 30-second attempts were too short for the sleeping service. `REVISIONPROOF_MCP_MAX_ATTEMPTS` now defaults to three bounded fresh-process attempts. Post-deploy gstack run `01M1GN7EY252SSM5F2AM170TKY` logged `ClickHouse MCP timeout on attempt 1/3`, recovered on the next process, and reached `EVIDENCE_ANCHORED` in a 51.878-second HTTP 201 response with `error=null`. See `docs/qa-report-2026-09-02-mcp-recovery.md`.

Final gstack run `01M0Z3338TYVHWHK4FZRGADTKZ` exercised real `google.vertex.gemini`, real `mcp-clickhouse.run_query`, candidate B (1.12x), blocked v2, repaired v3, private GCS persistence, and ClickHouse persistence. Raw JSON is `READY` with spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5` and `delivery_approved=true`. Event 14 records `Human approved the verified version for delivery` at `2026-08-26T13:48:30.750541Z`. ClickHouse contains one spec, 24 feature rows, and six check rows for the run.

## Remaining work

No push/deployment work remains. The extension-only ClickHouse migration and grants are already applied; do not rerun the historical bootstrap. Public LIVE memory is read-only without an owner key; private token/Secret Manager setup is a separate authority decision and is the remaining optional step before saving approved edits. Do not seed fake approvals or reuse historical human approval. For later console inspection use draft `10b3df86-6a21-4796-bc3c-88a34f8050ea`. Monaco `fill` appends: Ctrl+A, Backspace, fill single-line SQL, then inspect the rendered complete query before Run (the editor textbox value may only contain a cursor-local fragment).

Submission copy, a 2:45 recording script, and explicit release gates are in `docs/submission-pack-2026-08-27.md` and `docs/demo-recording-script-2026-08-27.md`. Update the recording script to demonstrate request classification, checkbox selection, automatic full-video generation, and the final human delivery gate. The latest full-video QA run reached `READY` but did not grant a new delivery approval.

Before submission: resolve development-tool eligibility with the organizer, obtain owner approval for public repository/video publication and branch landing, perform a clean-clone check and a fresh operator-led LIVE recording, and submit only after owner review. GitHub is currently PRIVATE with default branch `main`; work remains on `review/qa-hardening`. The existing Apache 2.0 notice was completed with the official license body on this branch; GitHub default-branch detection previously reported `Other` and must be rechecked after landing. No PR or merge has been requested.

Full restart hydration remains unimplemented, and the frontend does not restore an active run after refresh. The generated demo is a stylized storyboard plus a synthetic tone, with authored transcript-like seed metadata; it is not transcribed presenter footage. Capture v2's blocked state before v3 replaces the current proof and prunes old local evidence. The existing approved run is historical evidence only, not approval for a new recording run.

For later Cloud Shell operations, verify `gcloud config get-value account` is `secureis@gmail.com`, and describe the explicitly named project to verify number `348672234012` and label `managed-by=revisionproof-gcp`. Pass `--project=revisionproof-agentic-2026-kan` on every applicable command. **Do not change global gcloud account/project defaults** because another hackathon may use them. If the active account differs, stop for owner direction. Do not use `CLOUDSDK_CORE_ACCOUNT`; guarded scripts reject delegated environment overrides. If token refresh reports `metadata server ... missing 'email' field`, reauthorize the existing secureis session rather than switching identities or projects.

## Watchouts

The `LIVE` badge alone is not success evidence; require actual Gemini/MCP events plus persisted target rows. The official MCP reader now retries three fresh processes by default, but a sustained outage still fails closed after the configured limit. Cloud Run uses concurrency 4, min/max 1: four slots prevent the long-lived SSE stream from starving mutations, while one instance preserves the current process-local repository boundary. A restart still requires a new run. Do not drop ClickHouse backup table `revisionproof.segments_pre_seed_dedupe_20260826`. The bootstrap admin is deleted; durable view definer `revisionproof_view_definer_user` must remain. The KRW 30,000 budget is alert-only, not a hard cap. Codex-assisted source may affect hackathon eligibility; the user plans a separate Gemini review/rework before submission, but that alone does not establish eligibility. Runtime delivery approval does not publish or transmit the video externally.

## Git state

- Branch: `review/qa-hardening`
- Deployed implementation commit: `c5652b1`
- Remote: `https://github.com/devkan/RevisionProof.git`
- Push: `review/qa-hardening` is connected to `origin`; implementation commits `c982637` and `c5652b1` are pushed. The release documentation checkpoint follows this handoff update. No PR or merge has been performed; the repository remains PRIVATE. Hosted CI does not trigger on this branch push (its configured triggers are main pushes and PRs); local tests and Cloud Build were verified separately.

## Start here

For the current feature, read `docs/deployment-2026-09-03-clickhouse-intelligence.md` first, then the intelligence QA/inventory and runbook. Test the LIVE site at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`; refresh starts a new run, not restoration of the recorded proof. Optional local FIXTURE URL: `http://127.0.0.1:18125`. Stopping the demo requires only `docker stop revisionproof-intelligence-demo-20260903`; no volume deletion is necessary.

Read `docs/README.md`, `docs/qa-report-2026-09-02-automatic-full-video-ui.md`, `docs/submission-pack-2026-08-27.md`, and `docs/demo-recording-script-2026-08-27.md`. Use `docs/qa-report-2026-08-26-live-final.md` plus the infrastructure inventory for the full historical delivery-approved proof. The final delivery approval has been performed for the recorded historical run only.
