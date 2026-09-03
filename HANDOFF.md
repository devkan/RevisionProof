# Handoff

Last updated: 2026-09-03
Project: RevisionProof — D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof
Branch: review/qa-hardening

## Current Status

- The owner authorized and implementation now includes center zoom, literal text, timed subtitle cues, exact cuts and reviewed silence removal. The default UI has selectable examples, editable cards, explicit draft review, preserved-input adjustment and mapped comparisons. Read [the current guide](docs/basic-editing-guide-2026-09-03.md) and [engineering review](docs/basic-editing-plan-2026-09-03.md).
- New EDIT_PLAN spec 3.0 freezes original-time operations and a full-preview SHA-256. Export is a byte-identical copy. Legacy 2.x JSON/hash behavior remains compatible. All audio channels must be quiet; proposed cuts require user selection.
- Actual KANAPP compound request passed locally: run `01M1KD2G84K7G3CCT5RAG0WS89`, B, READY / 3 PASS, zero map flags. Text is visibly present at 6 seconds. Synthetic subtitles + manual/silence cuts run `01M1KDAT3C4Z43KQJTYB8ZSW3J` passed, 10s -> 7.766667s; revised 3s maps to original 5.233333s.
- Final regression and deployment of the expansion are in progress at this checkpoint. Current LIVE remains `revisionproof-staging-00017-cnr`, source `1c1204620382244fc817ce4f8f457f6867dc57cc`, build `95808615-6694-4d67-ad58-c04097cbf46a`, image `sha256:ad118dc715b9bdbbb4489ce523581f3ccbbc1efcbd93c26b67edf02b9869a5c2`. This preceding release does not have the new editor. Update after rollout.
- Branch/repo remain `review/qa-hardening` / PRIVATE. No PR, merge or visibility change. Push and existing-service Cloud Shell deployment were already authorized; no repeat approval is needed.
- Earlier automatic review rejected retransmission of `demo_movie_kanapp.mp4` to LIVE without explicit file-and-destination approval. Keep it local and use non-sensitive synthetic media for LIVE QA. Never auto-approve final delivery or seed Cloud memory.

## Previous Release Context

- Diagnosed the actual KANAPP audio false block and the LIVE Korean target-phrase error from logs, added failing regressions, then fixed them with schema 2.2 and explicit unsupported-request recovery. Current backend 303 / frontend 19 and static/build checks passed. Local actual-video proof and post-deploy synthetic-video evidence are in the new debug record.
- Added bounded original MP4/MOV/WebM upload, aspect-preserving 720p preparation, explicit 4–8 second selection, actual-source A/B/full rendering, spec 2.1 full-video checks, and preserved-source interpretation retry. Approved references are collapsed and fetched only when opened; zero records no longer imply vector search execution.
- The preceding upload release fixed fractional-duration end-frame failures (4.01/6.01 seconds), with real upload/render regressions. Its backend gate was **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint and production build passed. The current 303-test gate above includes the subsequent KANAPP fixes.
- Deployed a SHA-256-verified archive of the committed source using the existing account/project, resources, service accounts, ClickHouse host and two pinned secret versions. No global gcloud defaults or data/grants changed.
- Fresh LIVE gstack checks passed: separate video upload, A/B, whole-video render, three verification checks, MCP Change Map, playback/download, 25 MiB and 61-second warnings, optional memory with `actual_engine=none`, and 390px mobile layout. Browser console had no errors and recorded no resource responses >=400. The desktop/browser interruption was recovered with a fresh QA run; deployment was already successful.
- `/health`, `/ready` and `/api/runtime` returned HTTP 200. Runtime exposes 24 MiB / 4–60 seconds, LIVE ready, intelligence enabled and read-only memory policy.
- Updated release evidence, usage guide, architecture, README and docs index. Local QA used ports 18125/18126; recheck local server state after the desktop restart before relying on those URLs.

## Relevant Docs

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

1. Finish final test/lint gates, commit and push the basic editor.
2. Deploy the SHA-verified committed archive with the existing Cloud Build workflow; no ClickHouse migration is needed.
3. Verify fresh LIVE drafting, English/Korean text, captions/cuts, MCP verdict/map and browser playback using synthetic media. Record source/build/revision/run IDs in the current guide and this handoff.
4. Leave final human delivery approval false. Private memory keys, auto-transcription, original burned-in text replacement and general video effects remain separate work.

## Watchouts

- Target ONLY `revisionproof-agentic-2026-kan` (number `348672234012`, label `managed-by=revisionproof-gcp`), region `us-central1`, account `secureis@gmail.com`. Pass explicit `--project` on applicable commands; never change global gcloud defaults or use `CLOUDSDK_CORE_ACCOUNT` to switch identities.
- ClickHouse host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`, service `268999c1-badb-423e-993c-ebab14b551c4`. Seven extension objects/grants are already applied; do not rerun historical bootstrap or revoke existing grants.
- Preserve `revisionproof.segments_pre_seed_dedupe_20260826`, shared roles/definer, other projects and Docker volumes. Deletion, billing and new credentials require scoped owner authority.
- Runs are process-local; refresh does not restore the active UI, and restart may make old run APIs unavailable. Keep Cloud Run concurrency 4 / min-max 1 unless that state model is deliberately changed.
- The bundled source is an authored storyboard/tone with seeded metadata. User uploads instead use explicit user-selected timing and no inferred transcription. Basic editing is authorized and implemented; new exports have exact preview identity checks while the Change Map remains sampled diagnostics. Prepared uploads are process-local, not durably archived originals.
- Never auto-approve LIVE delivery or seed fake Cloud memory. Historical human-approved run `01M0Z3338TYVHWHK4FZRGADTKZ` is not approval for a new run.
- A LIVE badge or selected HNSW/QBit option alone is not proof of successful live calls/index use. Hosted CI does not run on this branch push; previous local test and Cloud Build successes are separate evidence.
- Secrets, archives, backups and ignored `.gstack/` evidence must not be published. New windows must reacquire browser sessions; trial end/date and Cloud state should be rechecked before operational changes.

## Suggested Next Action

Finish the release steps above. Local gstack QA uses port 18128 and `.gstack/basic-editor-browser/`; recheck process state after an interruption. The [basic editing guide](docs/basic-editing-guide-2026-09-03.md) has user instructions and current evidence. Existing deployment resources and secret versions must be preserved.
