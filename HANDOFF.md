# Handoff

Last updated: 2026-09-03
Project: RevisionProof — D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof
Branch: review/qa-hardening

## Current Status

- Original-video upload and optional approved-memory UX are committed and pushed as `d7676495ed7b2cf29a8ec03a9e865d9bb05f580c`, remote SHA verified. Deployment is waiting for explicit Cloud Shell authorization after automatic approval review rejected the Authorize click. Read [release preparation and exact next steps](docs/deployment-2026-09-03-source-upload.md) first; the deployed release below remains unchanged.
- GitHub push, additive ClickHouse migration, GCP deployment and fresh LIVE QA completed in the preceding release operation. Start with [the new-window guide](docs/handoff-2026-09-03.md).
- Deployed source: `c5652b1`; build `85ae9052-5b5b-43aa-a2bd-5c3004e913ee`; revision `revisionproof-staging-00015-h6b`, 100% traffic at [the LIVE site](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app).
- GitHub checkpoint including release docs: `c7ea2261e38242e0038f7d7f0a533a6da155f376`, pushed and remote-verified in the preceding operation. Repository remains PRIVATE; no PR, merge or publication.
- LIVE run `01M1JQSKYVTS5EFNJ6KBEYACHS` generated the complete Option B video, reached READY with three PASS checks, and persisted 60 frame samples / 30 map windows. Final delivery approval is false.
- Approved Edit Memory is read-only in public LIVE until separate owner-key setup. Cloud HNSW/QBit schema exists; actual vector/index execution was verified on a populated isolated server, not on the empty Cloud library.
- The earlier handoff docs and subsequent upload/UX implementation are now included in the pushed source commit. Cloud/runtime release evidence above remains historical; the new code is not deployed yet.

## Completed This Session

- Added bounded original MP4/MOV/WebM upload, aspect-preserving 720p preparation, explicit 4–8 second selection, actual-source A/B/full rendering, spec 2.1 full-video checks, and preserved-source interpretation retry. Approved references are collapsed and fetched only when opened; zero records no longer imply vector search execution.
- Backend full regression: 288 passed; latest upload/intelligence follow-up: 70 passed. Frontend 19 passed, build/lint and Ruff passed. gstack verified a different 12-second portrait source through READY/three PASS, download/playback, 25 MiB and 61-second warnings, and mobile layout. Local review server uses port 18126; no LIVE approval or save was performed.
- Release preparation found and fixed fractional-duration end-frame failures (4.01/6.01 seconds). Final full backend regression: 292 passed in 101.74s; frontend 19 passed; Ruff/check/format, ESLint and production build passed. The owner requested push/deploy; Cloud Shell authorization is awaiting explicit confirmation after automatic approval review rejected its Authorize click.
- Added a new-window guide covering product behavior, code ownership, exact deployment targets, completed work, approval-gated next steps and preserved resources.
- Indexed the guide and recorded the final pushed documentation checkpoint in the release record.
- Reconfirmed local HEAD/tracking ref at `c7ea226`, initially clean worktree, and RevisionProof-only Docker status. The FIXTURE demo is running at `http://127.0.0.1:18125`; two intelligence DB test containers remain stopped.
- Commit/push succeeded and a SHA-256-verified committed-source ZIP is prepared. No Cloud Build submission, deploy, paid LIVE run, credential change or cleanup was performed in the current attempt; Cloud Shell authorization remains pending.

## Relevant Docs

- [Source upload release preparation](docs/deployment-2026-09-03-source-upload.md) — pushed source SHA, final 292/19 tests, archive hash, automatic approval block and exact next deployment steps.
- [Original upload and memory UX](docs/source-upload-and-memory-ux-2026-09-03.md) — current local implementation, Korean usage guide, limits, verification and deployment boundary.
- [New-window guide](docs/handoff-2026-09-03.md) — read first; Korean summary, next actions and a copy/paste continuation prompt.
- [Deployment and LIVE evidence](docs/deployment-2026-09-03-clickhouse-intelligence.md) — build/image/run IDs, Cloud grants, resource inventory and rollback.
- [Intelligence runbook](docs/clickhouse-intelligence-runbook.md) — migration, private memory key, export/restore and feature flag.
- [QA and local resource inventory](docs/qa-report-2026-09-03-clickhouse-intelligence.md) — 278 backend / 16 frontend tests, real HNSW/QBit, backup restore and UI evidence.
- [Architecture](docs/architecture.md) and [security](docs/security.md) — trust boundaries and current process-local state.
- [Submission pack](docs/submission-pack-2026-08-27.md) and [older recording script](docs/demo-recording-script-2026-08-27.md) — need alignment with the new automatic full-video/intelligence flow.
- [Docs index](docs/README.md) — earlier deployments, source-video/UI changes, MCP retry fix and historical approved proof.

## Remaining Work

1. The owner requested deployment and source push is complete. Obtain the explicit Cloud Shell Authorize confirmation described in the release preparation note, then upload the prepared archive, build/deploy and verify a fresh LIVE upload. Do not bypass the automatic approval rejection using indirect credentials or execution.
2. If the owner wants LIVE memory saves, obtain separate credential-setup approval; first ensure the deployment preserves a pinned memory secret alongside existing ClickHouse bindings, then configure the private operator token and validate an explicitly human-approved save/retrieval.
3. Continue owner testing and update the demo script for checkbox selection, automatic full-video generation, Change Map and the actual memory activation state.
4. Before submission, recheck official rules/tool eligibility, obtain publication/landing approvals, perform clean-clone and operator-led recording checks, and decide ClickHouse trial-expiry hosting/export.

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

Continue the authorized upload/UX deployment after the pending Cloud Shell permission is explicitly approved. Read the release preparation note and verify existing Cloud configuration before submitting the committed archive. No new ClickHouse migration is needed for the retained check IDs. Private approved-memory saves remain a separate credential setup.
