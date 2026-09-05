# Handoff

Last updated: 2026-09-05
Project: RevisionProof — D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof
Branch: review/qa-hardening

## Current Status

- Latest LIVE release: [inline Studio deployment, canary and recovery](docs/deployment-2026-09-05-inline-studio.md). Source `8e63093` pushed to `review/qa-hardening`; Cloud Build `7ec59d25-6506-4953-b0f3-970455c263f8` SUCCESS; revision `revisionproof-staging-00029-2t2` healthy at 100% traffic. New JS `index-BNLptUXK.js` / CSS `index-BaYy-LUs.css` verified. Fresh frontend 69 and backend 349 tests passed. LIVE gstack verified inline settings, cut/zoom conflict explanation -> Fix edit -> corrected times -> enabled Check plan, keyboard/value preservation, responsive sizing and classic route. No new LIVE render/provider execution is claimed. Prior full FIXTURE/eight-control QA is in [the implementation report](docs/studio-inline-settings-2026-09-05.md). User's draft tab was untouched; local port 18131 remains a separate FIXTURE environment. Open LIVE in a separate tab.

- Previous Studio release, now a recovery point: source `44cc8c0` / revision `revisionproof-staging-00028-n4z`; build `660dbd2f-1bf5-4ab1-9cb1-59c41277b340` succeeded. Read [previous Studio deployment and recovery](docs/deployment-2026-09-05-studio.md) and [hands-on gstack QA](docs/qa-live-2026-09-05-studio.md) for full functional LIVE runs on 00026/00027; 00028 changed only one final-summary plural label. These provider runs are historical evidence, not runs on 00029.
- Previous full Studio QA: backend 349 tests and frontend 51 tests / 12 files passed, plus lint/build. LIVE gstack tested all eight edit controls across compound and silence runs, smart search, subtitle correction, A/B selection, full checks, external BLOCKED-to-READY recovery, playback, mobile layout, and read-only empty memory. The discovered source-preparation range bug and single-preview instructions were fixed and verified. Delivery approval remained false; no Approved Edit Memory writes.
- Restoration points: newly pushed `backup/pre-inline-studio-20260905` at `44cc8c0` (previous LIVE), plus `backup/pre-studio-ui-20260904` at `270d37d` and `backup/pre-studio-reqa-20260905` at `ca87a05`. Preserve all; restore into a separate worktree instead of resetting the active branch. Pre-card-redesign Check plan checkpoint `40767f6` remains reachable.
- A new 30-second English KANAPP promo source is ready for demo editing at `D:\Hackathon\006.Agentic Cinema Hackathon\video\kanapp_promo_english_editable_30s.mp4`; its matching overlay logo is `D:\Hackathon\006.Agentic Cinema Hackathon\video\kanapp_demo_logo.png`. The MP4 is 1280×720, 30 fps, H.264/AAC, 831,549 bytes, with six English scenes, English narration, a deliberately quieter 5–10 second section and a detected quiet interval around 15.19–18.45 seconds. Read [the English promo and three demo scenarios](docs/kanapp-english-demo-video-2026-09-04.md) first.
- The generated media passed FFmpeg full decode and RevisionProof upload validation locally. Its storyboard was visually inspected. The MP4 has **not** yet been uploaded to LIVE or completed an A/B/full-verification run, so no LIVE success is claimed for this new asset. Generated media stays outside Git; reproducible source and scenarios are tracked in `2186575`.
- Source-video uploads now accept up to **32,000,000 bytes (32 MB)** and are **deployed and LIVE verified**: source `08113823abbba221a9926799e9f5ae1dc0f33657`, revision `revisionproof-staging-00025-88t`, traffic 100%, all readiness conditions True. Build `98fdd1af-59ca-4300-ae39-c4cca0d334a5` SUCCESS at `2026-09-04T07:17:13.397392Z`; image `sha256:c04b1b1caae3bbd97b3d21741ee12709a468e2fbe49947411b677554d40e4ef4`. Read [the 32 MB upload release record](docs/deployment-2026-09-04-upload-32mb.md) first.
- LIVE browser QA rejected a synthetic 32,000,001-byte file before network upload with a clear 32.1 MB warning. A synthetic exact 32,000,000-byte multipart request passed Cloud Run and reached application media validation, proving the boundary does not trigger the platform's HTTP 413 limit. `/health`, `/ready` and `/api/runtime` returned 200; runtime reports `max_bytes=32000000`.
- Smart scene finder and recipe memory are **deployed and LIVE verified**: source `b0b00a9937cf158560f4a3fba2f3d473104b3b6c`, revision `revisionproof-staging-00024-c9p`, traffic 100%, all readiness conditions True. Build `aa63da88-9407-45e6-9659-235427e5d4a2` SUCCESS at `2026-09-04T05:51:14.595604Z`; image `sha256:03da71d487c0911359164cae0956de4e29ce7410207ab5ec65d4df3b268f2970`. Read [the smart scene and recipe memory release record](docs/smart-scene-and-recipe-memory-2026-09-04.md) first.
- Smart scene finder defaults OFF and requires Start/End times. ON clearly discloses Google AI and ClickHouse credit use before **Find scenes**. LIVE sample search indexed 8 segments through `mcp-clickhouse.run_query`, returned three choices, and carried the selected 20–24 second range into a `Zoom in · 20s–24s` editable draft. Browser network/console and 390px overflow checks passed.
- ClickHouse Cloud now has 24 target objects including 5 new smart-scene/recipe objects. Smart scene rows expire after 7 days; MCP can read only the three security-definer views and cannot read the new raw tables. Approved recipe saving still requires all proof/approval gates and a private owner key; public LIVE memory remains read-only.
- Advanced editing is **deployed and LIVE verified**: source `150d36774b0acaece9aad57a4d655af3eda59c5b`, revision `revisionproof-staging-00023-j7p`, traffic 100%, all readiness conditions True. Build `fcb6b33c-7b81-421c-8d5d-21eff29cc1bf` SUCCESS at `2026-09-04T03:41:32.832473Z`; image `sha256:fc05a5676d7a68c5c6f7502902ab81bfe2b36bff3a6bd459d144c1207344826e`. Read [the advanced release record](docs/deployment-2026-09-04-advanced-editing.md) first.
- The guided editor now has eight controls: zoom, text, timed subtitle, exact cut, reviewed quiet-pause removal, 0.5-2x speed, -60 to +12 dB volume, and bounded uploaded logos. LIVE Vertex Gemini drafts editable Korean, English, auto-detected, or mixed Korean/English subtitle cues. Spec 3.1 freezes retiming, audio changes, normalized logo ID/hash, overlays, mapped timeline, and the chosen full-preview SHA-256. Legacy 2.x and safe 3.0 contracts remain compatible.
- Exact-source gates: backend 336 passed / 129.74s, focused regressions 25 passed / 22.77s, rate-limit checks 5 passed / 2.86s, frontend 23 passed, plus Ruff/ESLint/build. Desktop and 390 px local gstack QA passed, including valid and over-limit logos, compound previews, output frames, overflow, and console checks.
- Fresh LIVE run `01M1N8HK13Z3R5GG8KMEEDDCYN` used synthetic Korean plus English speech. Four generated cues remained editable; two ambiguous product-name transcriptions were corrected to KANAPP. The plan combined those subtitles with 1.5x speed, -6 dB volume, and a full-video bottom-right logo. B reached READY / 3 PASS under spec 3.1; 9.93s -> 8.6s. Browser console/network and 390 px overflow checks passed. Delivery approval remains false.
- Previous QA fixes remain present: source switches clear stale drafts, frame-aligned cuts do not falsely BLOCK, and local caption-removal requests cannot suggest footage deletion. The earlier `94c081c` release and runs are historical evidence.
- Actual KANAPP compound request passed locally: run `01M1KD2G84K7G3CCT5RAG0WS89`, B, READY / 3 PASS, zero map flags. Text is visibly present at 6 seconds. Synthetic subtitles + manual/silence cuts run `01M1KDAT3C4Z43KQJTYB8ZSW3J` passed, 10s -> 7.766667s; revised 3s maps to original 5.233333s.
- Previous release `1b2c0ae` / revision `00021-4fx` used build `2467c268-f0f9-4090-9c88-7dd71f454f53` and passed 322/22 tests. Its LIVE run `01M1KHABHY8YWTZ7RQVPK3MF9Q` is historical evidence, superseded by the new runs above. Read the guide's LIVE debugging record before changing the provider schema: Gemini receives only five draft fields, while strict runtime validation and silence settings stay server-owned.
- Branch/repo remain `review/qa-hardening` / PRIVATE. No PR, merge or visibility change. Existing-service deployment and Git push are authorized; the earlier Cloud Console approval block was resolved by the user's explicit deployment request.
- Earlier automatic review rejected retransmission of `demo_movie_kanapp.mp4` to LIVE without explicit file-and-destination approval. Keep it local and use non-sensitive synthetic media for LIVE QA. Never auto-approve final delivery or seed Cloud memory.

## Completed This Session

- Raised the source-video limit to 32,000,000 decimal bytes, added browser/server boundary handling and tests, pushed source `0811382`, deployed revision `revisionproof-staging-00025-88t`, and verified LIVE health, readiness, runtime configuration, a 32,000,001-byte browser rejection with no upload request, and an exact 32,000,000-byte request reaching application validation.
- Generated the English KANAPP promo, demo logo and storyboard; added the reproducible Windows/SAPI/FFmpeg generator in `scripts/generate_kanapp_promo.py`.
- Wrote three independent English demo paths covering smart scene search and all eight editor controls. Scenario 2 is the recommended single-run feature demo.

## Previous Release Context

- Diagnosed the actual KANAPP audio false block and the LIVE Korean target-phrase error from logs, added failing regressions, then fixed them with schema 2.2 and explicit unsupported-request recovery. Current backend 303 / frontend 19 and static/build checks passed. Local actual-video proof and post-deploy synthetic-video evidence are in the new debug record.
- Added bounded original MP4/MOV/WebM upload, aspect-preserving 720p preparation, explicit 4–8 second selection, actual-source A/B/full rendering, spec 2.1 full-video checks, and preserved-source interpretation retry. Approved references are collapsed and fetched only when opened; zero records no longer imply vector search execution.
- The preceding upload release fixed fractional-duration end-frame failures (4.01/6.01 seconds), with real upload/render regressions. Its backend gate was **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint and production build passed. The current 303-test gate above includes the subsequent KANAPP fixes.
- Deployed a SHA-256-verified archive of the committed source using the existing account/project, resources, service accounts, ClickHouse host and two pinned secret versions. No global gcloud defaults or data/grants changed.
- Fresh LIVE gstack checks passed: separate video upload, A/B, whole-video render, three verification checks, MCP Change Map, playback/download, 25 MiB and 61-second warnings, optional memory with `actual_engine=none`, and 390px mobile layout. Browser console had no errors and recorded no resource responses >=400. The desktop/browser interruption was recovered with a fresh QA run; deployment was already successful.
- In the historical source-upload release, `/health`, `/ready` and `/api/runtime` returned HTTP 200 and runtime exposed 24 MiB / 4–60 seconds. The current release supersedes that file-size limit with 32 MB while retaining the 4–60-second duration range.
- Updated release evidence, usage guide, architecture, README and docs index. Local QA used ports 18125/18126; recheck local server state after the desktop restart before relying on those URLs.

## Relevant Docs

- [Inline Studio LIVE deployment](docs/deployment-2026-09-05-inline-studio.md) — current source/build/revision, fresh tests, LIVE UI canary and previous-LIVE recovery point.
- [Inline Studio settings and card polish](docs/studio-inline-settings-2026-09-05.md) — implementation history, restore point and full local FIXTURE browser evidence.

- [Studio LIVE deployment and restoration](docs/deployment-2026-09-05-studio.md) — current source, build/revision identities, real workflows, fixes and backup recovery.
- [Studio hands-on LIVE gstack QA](docs/qa-live-2026-09-05-studio.md) — scope, defects, tests, screenshots and intentional approval boundaries.
- [KANAPP English promo and three demo scenarios](docs/kanapp-english-demo-video-2026-09-04.md) — source paths, checksums, timeline, narration, exact edit steps, English presenter scripts and local verification boundary.
- [32 MB upload limit LIVE release](docs/deployment-2026-09-04-upload-32mb.md) — current source/build/revision, decimal-MB rationale and browser/server boundary proof.
- [Smart scene finder and recipe memory LIVE release](docs/smart-scene-and-recipe-memory-2026-09-04.md) — current source/build/revision, ClickHouse Cloud migration, opt-in cost UX, recipe memory and LIVE search proof.
- [Advanced editing LIVE deployment and proof](docs/deployment-2026-09-04-advanced-editing.md) — read first; source/build/image/revision IDs, mixed-speech run, spec 3.1, and gstack evidence.
- [Advanced editing usage guide](docs/advanced-editing-guide-2026-09-04.md) — eight controls, subtitle workflow, limits, examples, and unsupported advanced work.
- [Latest QA-fix deployment and LIVE evidence](docs/deployment-2026-09-03-qa-fixes.md) — read first; source/build/image/revision IDs, cut and compound runs, exact download hash.
- [gstack review and QA fixes](docs/qa-review-2026-09-03-basic-editor.md) — 3 fixes, before/after tests and resolved historical Cloud Console rejection.
- [Basic editing guide and release evidence](docs/basic-editing-guide-2026-09-03.md) — current work; read first.
- [gstack engineering review](docs/basic-editing-plan-2026-09-03.md) — scope and design decisions.

- [KANAPP demo fix and deployment](docs/kanapp-demo-fix-2026-09-03.md) — read first; source/build/image/revision IDs, 303/19 tests, actual-video local proof, fresh synthetic LIVE checks and actual-file retransmission approval boundary.
- [Source upload deployment](docs/deployment-2026-09-03-source-upload.md) — preceding release's source/build/image/revision IDs, 292/19 tests and upload evidence.
- [Original upload and memory UX](docs/source-upload-and-memory-ux-2026-09-03.md) — Korean usage guide, limits, local/LIVE verification and deployment boundary.
- [Earlier new-window guide](docs/handoff-2026-09-03.md) — code ownership and resource inventory; historical release state is superseded by this HANDOFF.
- [Deployment and LIVE evidence](docs/deployment-2026-09-03-clickhouse-intelligence.md) — build/image/run IDs, Cloud grants, resource inventory and rollback.
- [Intelligence runbook](docs/clickhouse-intelligence-runbook.md) — migration, private memory key, export/restore and feature flag.
- [QA and local resource inventory](docs/qa-report-2026-09-03-clickhouse-intelligence.md) — 278 backend / 16 frontend tests, real HNSW/QBit, backup restore and UI evidence.
- [Architecture](docs/architecture.md) and [security](docs/security.md) — trust boundaries and current process-local state.
- [Submission pack](docs/submission-pack-2026-08-27.md) and [older recording script](docs/demo-recording-script-2026-08-27.md) — need alignment with the new automatic full-video/intelligence flow.
- [Docs index](docs/README.md) — earlier deployments, source-video/UI changes, MCP retry fix and historical approved proof.

## Remaining Work

- Inline settings/card push and deployment are complete. Preserve `40767f6`, the previous LIVE revision and backup branches. Do not reload the user's draft tab automatically. No further release action is pending.

1. Rehearse Scenario 2 with the new English MP4 in the LIVE editor: generate English subtitles, correct `KANAPP`, `Medical Check` or `LeanCOO` if needed, select only the main quiet interval, apply 1.25× speed, +6 dB volume and the closing URL, then inspect A/B and full verification.
2. Rehearse Scenario 1 and Scenario 3 from fresh uploads of the original MP4, then choose the strongest moments for the final recorded demo.
3. Record the final English presentation when the owner is ready. Google authorization, Studio push/deployment, corrective LIVE QA and final canary are complete. Preserve classic `/` and the human final-delivery approval gate.

## Watchouts

- Target ONLY `revisionproof-agentic-2026-kan` (number `348672234012`, label `managed-by=revisionproof-gcp`), region `us-central1`, account `secureis@gmail.com`. Pass explicit `--project` on applicable commands; never change global gcloud defaults or use `CLOUDSDK_CORE_ACCOUNT` to switch identities.
- ClickHouse host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`, service `268999c1-badb-423e-993c-ebab14b551c4`. Twelve extension objects and their grants are already applied, for 24 target objects total; do not rerun historical bootstrap or revoke existing grants.
- Preserve `revisionproof.segments_pre_seed_dedupe_20260826`, shared roles/definer, other projects and Docker volumes. Deletion, billing and new credentials require scoped owner authority.
- Runs are process-local; refresh does not restore the active UI, and restart may make old run APIs unavailable. Keep Cloud Run concurrency 4 / min-max 1 unless that state model is deliberately changed.
- The upload limit is 32,000,000 decimal bytes, leaving room for the multipart envelope under Cloud Run's 32 MiB HTTP/1 request-body ceiling. Do not reinterpret the setting as 32 MiB without changing the upload transport.
- The bundled source is an authored storyboard/tone with seeded metadata. User uploads use explicit original-video timing; speech transcription runs only when the user selects the subtitle generator and always returns an editable draft. New exports have exact preview identity checks while the Change Map remains sampled diagnostics. Prepared videos and logo assets are process-local, not durably archived originals.
- The new KANAPP MP4/logo are local generated files outside the Git repository. Preserve the two upload-ready files in `D:\Hackathon\006.Agentic Cinema Hackathon\video`; regenerate with `backend\.venv\Scripts\python.exe scripts\generate_kanapp_promo.py` if lost. Windows speech synthesis requires access to the installed `Microsoft Zira Desktop` voice and may fail in a restricted sandbox.
- Start each demo scenario from the original 30-second source. Edit timings refer to the original upload; chaining one scenario's output into the next makes the documented times wrong.
- Never auto-approve LIVE delivery or seed fake Cloud memory. Historical human-approved run `01M0Z3338TYVHWHK4FZRGADTKZ` is not approval for a new run.
- A LIVE badge or selected HNSW/QBit option alone is not proof of successful live calls/index use. Hosted CI does not run on this branch push; previous local test and Cloud Build successes are separate evidence.
- Secrets, archives, backups and ignored `.gstack/` evidence must not be published. New windows must reacquire browser sessions; trial end/date and Cloud state should be rechecked before operational changes.

## Suggested Next Action

Open [the current LIVE Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio), read the KANAPP English demo guide, and run Scenario 2 from the original local MP4 without approving final delivery on behalf of the owner.
