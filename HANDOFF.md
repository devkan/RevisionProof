# Handoff

Last updated: 2026-09-03
Project: RevisionProof — D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof
Branch: review/qa-hardening

## Current Status

- Follow-up fixes for the owner's KANAPP demo are ready for deployment: unchanged positive-peak audio no longer falsely blocks new spec 2.2 uploads; Korean uploaded targets use the explicit user range; unsupported text requests show guidance and `Edit request`. Backend 303 / frontend 19 tests passed. Read [the KANAPP debug/release record](docs/kanapp-demo-fix-2026-09-03.md) first. Text insertion remains unimplemented. The revision below is the preceding release until rollout verification is recorded.

- Original-video upload and optional approved-memory UX are pushed and deployed. Source commit: `d7676495ed7b2cf29a8ec03a9e865d9bb05f580c`. The owner explicitly approved Cloud Shell authorization, resolving the earlier approval block. Start with [the latest release and LIVE evidence](docs/deployment-2026-09-03-source-upload.md).
- Cloud Build `41e73ed2-e824-485e-b464-e3fc166f259b` succeeded; revision `revisionproof-staging-00016-j4q` serves 100% traffic at [the LIVE site](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app). Image digest: `sha256:08a49f48e2684c0424c03fd340c7f7853f77572bf436f07fab4966dd0154938b`.
- Branch remains `review/qa-hardening`; repository remains PRIVATE, with no PR, merge or visibility change. Post-deploy documentation is a separate commit from the deployed application source; use current Git HEAD for that documentation checkpoint.
- Fresh LIVE run `01M1K3CSTV2R01X4VF3CHNFWK5` uploaded a separate 12-second portrait video, selected 2–8 seconds, used Gemini, and generated the complete Option B video. READY / three PASS / official MCP Change Map with 24 samples and 12 windows / zero review flags. MP4 download and playback passed. Final delivery approval and memory save are false.
- Approved Edit Memory is read-only in public LIVE until separate owner-key setup. Cloud HNSW/QBit schema exists; actual vector/index execution was verified on a populated isolated server, not on the empty Cloud library.
- The additive ClickHouse migration belongs to the preceding release and was not rerun. The old revision `revisionproof-staging-00015-h6b` and earlier resources remain available; no cleanup was performed.

## Completed This Session

- Added bounded original MP4/MOV/WebM upload, aspect-preserving 720p preparation, explicit 4–8 second selection, actual-source A/B/full rendering, spec 2.1 full-video checks, and preserved-source interpretation retry. Approved references are collapsed and fetched only when opened; zero records no longer imply vector search execution.
- Release review fixed fractional-duration end-frame failures (4.01/6.01 seconds), with real upload/render regressions. Final backend regression: **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint and production build passed. No source changes followed these gates.
- Deployed a SHA-256-verified archive of the committed source using the existing account/project, resources, service accounts, ClickHouse host and two pinned secret versions. No global gcloud defaults or data/grants changed.
- Fresh LIVE gstack checks passed: separate video upload, A/B, whole-video render, three verification checks, MCP Change Map, playback/download, 25 MiB and 61-second warnings, optional memory with `actual_engine=none`, and 390px mobile layout. Browser console had no errors and recorded no resource responses >=400. The desktop/browser interruption was recovered with a fresh QA run; deployment was already successful.
- `/health`, `/ready` and `/api/runtime` returned HTTP 200. Runtime exposes 24 MiB / 4–60 seconds, LIVE ready, intelligence enabled and read-only memory policy.
- Updated release evidence, usage guide, architecture, README and docs index. Local QA used ports 18125/18126; recheck local server state after the desktop restart before relying on those URLs.

## Relevant Docs

- [Source upload deployment](docs/deployment-2026-09-03-source-upload.md) — read first; source/build/image/revision IDs, 292/19 tests, archive hash, fresh LIVE evidence and remaining boundaries.
- [Original upload and memory UX](docs/source-upload-and-memory-ux-2026-09-03.md) — Korean usage guide, limits, local/LIVE verification and deployment boundary.
- [Earlier new-window guide](docs/handoff-2026-09-03.md) — code ownership and resource inventory; historical release state is superseded by this HANDOFF.
- [Deployment and LIVE evidence](docs/deployment-2026-09-03-clickhouse-intelligence.md) — build/image/run IDs, Cloud grants, resource inventory and rollback.
- [Intelligence runbook](docs/clickhouse-intelligence-runbook.md) — migration, private memory key, export/restore and feature flag.
- [QA and local resource inventory](docs/qa-report-2026-09-03-clickhouse-intelligence.md) — 278 backend / 16 frontend tests, real HNSW/QBit, backup restore and UI evidence.
- [Architecture](docs/architecture.md) and [security](docs/security.md) — trust boundaries and current process-local state.
- [Submission pack](docs/submission-pack-2026-08-27.md) and [older recording script](docs/demo-recording-script-2026-08-27.md) — need alignment with the new automatic full-video/intelligence flow.
- [Docs index](docs/README.md) — earlier deployments, source-video/UI changes, MCP retry fix and historical approved proof.

## Remaining Work

The requested source-upload/UX push and deployment are complete. Separate follow-up work:

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

Use the deployed upload flow for owner testing. No further deployment or ClickHouse migration is needed for this release. If the next request is approved-memory saving, review its separate credential setup and human approval requirements first.
