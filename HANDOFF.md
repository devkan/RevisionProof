# Handoff

Last updated: 2026-09-03
Project: RevisionProof — D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof
Branch: review/qa-hardening

## Current Status

- KANAPP demo fixes are pushed and deployed from source `1c1204620382244fc817ce4f8f457f6867dc57cc`: unchanged positive-peak audio no longer falsely blocks new spec 2.2 uploads; Korean uploaded targets use the explicit user range; unsupported text requests show guidance and `Edit request`. Backend 303 / frontend 19 tests passed. Read [the KANAPP debug/release record](docs/kanapp-demo-fix-2026-09-03.md) first. Text/caption/logo insertion remains unimplemented.
- Cloud Build `95808615-6694-4d67-ad58-c04097cbf46a` succeeded at `2026-09-03T08:51:17.608781Z`; revision `revisionproof-staging-00017-cnr` serves 100% traffic at [the LIVE site](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=1c12046). Image digest: `sha256:ad118dc715b9bdbbb4489ce523581f3ccbbc1efcbd93c26b67edf02b9869a5c2`. Existing browser tabs may need a hard refresh; correct script is `index-55CB_99c.js`.
- Actual `demo_movie_kanapp.mp4` local run `01M1K6VB9HVFPY112AQRKXD9EC` is READY / three PASS. Post-deploy retransmission of that file to LIVE was rejected by automatic approval review, which requires explicit file-and-destination approval. Do not bypass that rejection. Read-only health/runtime checks and non-sensitive synthetic-video LIVE QA were completed separately.
- Fresh synthetic LIVE run `01M1K7XV7QF85PVHE9Q1EKD9HQ` completed READY / three PASS / official MCP Change Map with 20 samples and 10 windows, zero review flags. Source and candidate decoded peaks both +2.13 dBFS; peak/RMS deltas both 0. MP4 download/playback, 390px width and console/network checks passed. Exact compound Korean guidance and `Edit request` preservation passed in run `01M1K7W9763JK70AV2NGBDTTHJ`. Final delivery approval and memory save remain false.
- The preceding original-upload release was source `d7676495ed7b2cf29a8ec03a9e865d9bb05f580c`, build `41e73ed2-e824-485e-b464-e3fc166f259b`, revision `revisionproof-staging-00016-j4q`. Its [release record](docs/deployment-2026-09-03-source-upload.md) remains historical evidence. Cloud Shell deployment authorization was already explicitly approved by the owner.
- Branch remains `review/qa-hardening`; repository remains PRIVATE, with no PR, merge or visibility change. Post-deploy documentation is a separate commit from the deployed application source; use current Git HEAD for that documentation checkpoint.
- Preceding-release LIVE run `01M1K3CSTV2R01X4VF3CHNFWK5` uploaded a separate 12-second portrait video, selected 2–8 seconds, used Gemini, and generated the complete Option B video. READY / three PASS / official MCP Change Map with 24 samples and 12 windows / zero review flags. MP4 download and playback passed. Final delivery approval and memory save are false.
- Approved Edit Memory is read-only in public LIVE until separate owner-key setup. Cloud HNSW/QBit schema exists; actual vector/index execution was verified on a populated isolated server, not on the empty Cloud library.
- The additive ClickHouse migration belongs to the preceding release and was not rerun. The old revision `revisionproof-staging-00015-h6b` and earlier resources remain available; no cleanup was performed.

## Completed This Session

- Diagnosed the actual KANAPP audio false block and the LIVE Korean target-phrase error from logs, added failing regressions, then fixed them with schema 2.2 and explicit unsupported-request recovery. Current backend 303 / frontend 19 and static/build checks passed. Local actual-video proof and post-deploy synthetic-video evidence are in the new debug record.
- Added bounded original MP4/MOV/WebM upload, aspect-preserving 720p preparation, explicit 4–8 second selection, actual-source A/B/full rendering, spec 2.1 full-video checks, and preserved-source interpretation retry. Approved references are collapsed and fetched only when opened; zero records no longer imply vector search execution.
- The preceding upload release fixed fractional-duration end-frame failures (4.01/6.01 seconds), with real upload/render regressions. Its backend gate was **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint and production build passed. The current 303-test gate above includes the subsequent KANAPP fixes.
- Deployed a SHA-256-verified archive of the committed source using the existing account/project, resources, service accounts, ClickHouse host and two pinned secret versions. No global gcloud defaults or data/grants changed.
- Fresh LIVE gstack checks passed: separate video upload, A/B, whole-video render, three verification checks, MCP Change Map, playback/download, 25 MiB and 61-second warnings, optional memory with `actual_engine=none`, and 390px mobile layout. Browser console had no errors and recorded no resource responses >=400. The desktop/browser interruption was recovered with a fresh QA run; deployment was already successful.
- `/health`, `/ready` and `/api/runtime` returned HTTP 200. Runtime exposes 24 MiB / 4–60 seconds, LIVE ready, intelligence enabled and read-only memory policy.
- Updated release evidence, usage guide, architecture, README and docs index. Local QA used ports 18125/18126; recheck local server state after the desktop restart before relying on those URLs.

## Relevant Docs

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

The source-upload/UX and KANAPP bug-fix deployments are complete. One validation step requires explicit approval: retransmit `demo_movie_kanapp.mp4` to the existing LIVE service for post-deploy actual-file verification. It already passed local testing; automatic approval review blocked the network retransmission. Separate follow-up work:

1. If the owner wants LIVE memory saves, obtain separate credential-setup approval; first ensure the deployment preserves a pinned memory secret alongside existing ClickHouse bindings, then configure the private operator token and validate an explicitly human-approved save/retrieval.
2. Continue owner testing and update the demo script for source upload, checkbox selection, automatic full-video generation, Change Map and the actual memory activation state.
3. Before submission, recheck official rules/tool eligibility, obtain publication/landing approvals, perform clean-clone and operator-led recording checks, and decide ClickHouse trial-expiry hosting/export.

## Watchouts

- Target ONLY `revisionproof-agentic-2026-kan` (number `348672234012`, label `managed-by=revisionproof-gcp`), region `us-central1`, account `secureis@gmail.com`. Pass explicit `--project` on applicable commands; never change global gcloud defaults or use `CLOUDSDK_CORE_ACCOUNT` to switch identities.
- ClickHouse host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`, service `268999c1-badb-423e-993c-ebab14b551c4`. Seven extension objects/grants are already applied; do not rerun historical bootstrap or revoke existing grants.
- Preserve `revisionproof.segments_pre_seed_dedupe_20260826`, shared roles/definer, other projects and Docker volumes. Deletion, billing and new credentials require scoped owner authority.
- Runs are process-local; refresh does not restore the active UI, and restart may make old run APIs unavailable. Keep Cloud Run concurrency 4 / min-max 1 unless that state model is deliberately changed.
- The bundled source is an authored storyboard/tone with seeded metadata. User uploads instead use explicit user-selected timing and no inferred transcription. Only constrained punch-in is automated; Change Map and full-video checks use sampled diagnostics. Prepared uploads are process-local, not durably archived originals.
- Never auto-approve LIVE delivery or seed fake Cloud memory. Historical human-approved run `01M0Z3338TYVHWHK4FZRGADTKZ` is not approval for a new run.
- A LIVE badge or selected HNSW/QBit option alone is not proof of successful live calls/index use. Hosted CI does not run on this branch push; previous local test and Cloud Build successes are separate evidence.
- Secrets, archives, backups and ignored `.gstack/` evidence must not be published. New windows must reacquire browser sessions; trial end/date and Cloud state should be rechecked before operational changes.

## Suggested Next Action

Use the release URL above or a hard refresh for owner testing. If the owner explicitly approves retransmitting the actual KANAPP file to the existing LIVE service, finish that post-deploy check with the exact compound request, `Edit request`, then zoom-only/B/three checks; keep final delivery approval false. No further deployment or ClickHouse migration is needed for these fixes. Text insertion is separate feature work and has not been authorized or implemented in this fix.
