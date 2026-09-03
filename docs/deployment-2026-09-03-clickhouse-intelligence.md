# ClickHouse intelligence release — 2026-09-03

## Release scope

Owner requested GitHub push and deployment after the extension-only migration/grant confirmation. The existing private repository and `review/qa-hardening` branch are retained. No PR, merge, repository publication, billing change, or new private workspace credential is part of this release.

- Backend/infrastructure commit: `c982637`.
- UI/deployed-source commit: `c5652b1`.
- GitHub push: confirmed `25b89a9..c5652b1` on `origin/review/qa-hardening`.
- Release documentation checkpoint: `c7ea2261e38242e0038f7d7f0a533a6da155f376`, subsequently pushed to the same branch and verified against the remote SHA. This documentation-only commit does not change deployed source `c5652b1`. For the next session, start with [the continuity note](handoff-2026-09-03.md).
- Fresh local gates: backend **278 PASS** (78.51 s), frontend **16 PASS**, Ruff check/format, ESLint, TypeScript/Vite production build, and `git diff --check` PASS.
- The gstack ship checklist and independent scoped coverage/plan review found no concrete release blocker. This is not a full historical-branch landing approval or measured 100% coverage claim.
- GitHub Actions only triggers pushes to `main` or pull requests. No hosted CI run is claimed for this branch push; local gates and Cloud Build are separate evidence.

## ClickHouse migration — completed

Verified before writes: service `268999c1-badb-423e-993c-ebab14b551c4`, version `26.2.1.641`, database `revisionproof`, exact one-row deployment sentinel for project `revisionproof-agentic-2026-kan` and host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`.

Applied the 15 reviewed statements in `infra/clickhouse/intelligence.sql` individually through the signed-in console draft `10b3df86-6a21-4796-bc3c-88a34f8050ea`. Each CREATE/GRANT reported success. Verified the database increased from 12 to 19 objects, preserving all 12 originals including `segments_pre_seed_dedupe_20260826`.

New objects:

| Object | Actual Cloud engine |
| --- | --- |
| `revision_frame_pairs` | SharedMergeTree |
| `revision_change_windows` | SharedAggregatingMergeTree |
| `revision_change_windows_mv` | MaterializedView |
| `revision_change_map` | View |
| `approved_edits` | SharedMergeTree |
| `approved_edit_memory` | View |
| `approved_edit_neighbors` | View |

All four new views use `revisionproof_view_definer_user` and `SQL SECURITY DEFINER`. `approved_edits` contains materialized `QBit(Float32, 768)` and `approved_edit_hnsw`. This proves configuration, not actual HNSW selection on an empty production library; actual index-use evidence remains the isolated 12,000-vector test documented in the QA report.

Only these privileges were added, confirmed in `system.grants`:

- `revisionproof_view_definer`: SELECT frame pairs and approved edits; INSERT/SELECT aggregate windows.
- `revisionproof_writer`: INSERT frame pairs and approved edits.
- `revisionproof_mcp_reader`: SELECT change map, approved memory, and parameterized neighbors views.

No existing grants were revoked, widened to database/global scope, or reassigned. No users, API keys, roles, service accounts, or secrets were created. The existing definer and restricted raw-table boundary remain.

## GCP build/deployment

Target: project `revisionproof-agentic-2026-kan` (`348672234012`), region `us-central1`, service `revisionproof-staging`, account `secureis@gmail.com`. Project label `managed-by=revisionproof-gcp` was verified. The Cloud Shell default project was unset and was left unchanged; commands use explicit project targets.

- Committed source archive: `revisionproof-deploy-c5652b1.zip`.
- SHA-256, verified both locally and in Cloud Shell: `666d0c611b8bd178f0c6e369ff069e1548ff58e89277bb9487735047acec7969`.
- Cloud Shell archive: `/home/secureis/revisionproof-deploy-c5652b1.zip`.
- Fresh extraction directory: `/home/secureis/revisionproof-build-c5652b1` (exclusive creation; no old directory overwritten).
- Source staging object: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788408611.817899-2f4ea8394bba4a24a82d8b634d95f107.tgz`.
- Cloud Build: `85ae9052-5b5b-43aa-a2bd-5c3004e913ee`, submitted 2026-09-03T04:10:15Z.
- Build status: **SUCCESS**, finished 2026-09-03T04:17:06.740874Z.
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:85ae9052-5b5b-43aa-a2bd-5c3004e913ee`.
- Image digest: `sha256:3f437dc970c8de36c3c3542160d334de73122ca7d905cd6035b0f6ac74f13459`.
- Serving revision: `revisionproof-staging-00015-h6b`, 100% traffic; Ready, ConfigurationsReady and RoutesReady all True.
- `/health`, `/ready`, `/api/runtime`: HTTP 200. Runtime reports LIVE, intelligence enabled, and `memory_save_policy=read_only`.
- Fresh end-to-end LIVE verification: **PASS**, details below.

The exact committed `cloudbuild.yaml` is invoked with `_INTELLIGENCE_ENABLED=true` and the previously verified ClickHouse host and numeric secret versions `1`. Both existing secret bindings and the runtime/build service accounts remain unchanged. No workspace memory-write token is configured: public LIVE memory stays read-only.

## Fresh LIVE proof and browser QA

Run `01M1JQSKYVTS5EFNJ6KBEYACHS` reached **READY** at 2026-09-03T04:20:30Z. It used real `google.vertex.gemini` interpretation, `mcp-clickhouse.run_query` evidence lookup, explicit safe-request selection, A/B preview rendering, Option B (1.12x) full-source rendering, MCP-backed deterministic verification, and MCP Change Map aggregation. No final delivery approval was granted: `delivery_approved=false`, and no approved-memory row was fabricated or saved.

- Frozen spec: `2423bac3c6752026c8e8a511b17e276b9c4b222dc48207345a437eefb0b528ce`.
- Checks: `approved_patch`, `locked_cta`, `locked_audio` all PASS.
- Analysis: `01M1JQXREQ5MXBXMN5R7P8D498`; map status ready, source official MCP.
- Independently queried Cloud rows: **60 frame pairs, 30 merged windows, one spec, three checks**.
- Window range: second 0 through 29, 60 unique samples, six requested seconds (8–13), one matching spec, zero sampled review flags.
- Private GCS output: `runs/01M1JQSKYVTS5EFNJ6KBEYACHS/versions/approved-b.mp4`, generation `1788409203060962`, 817,180 bytes, content type `video/mp4`.
- Generated-video route: `/api/runs/01M1JQSKYVTS5EFNJ6KBEYACHS/generated-video`. The current run remains process-local and requires a new run after restart; the Cloud evidence/media persist independently.

The initial classification request returned HTTP 201 in 24.372 seconds. The UI displayed processing status and disabled mutation controls. Preview/search spinners were observed visible with a running `spin` animation. The three requests became one executable request, one clarification-required request and one editor-required request; only the selected first request changed the video.

Desktop 1280×900 and mobile 390×844 QA passed:

- B preview enlarged from 369px to 998px; source/A/B media loaded at 1280×720 without media errors.
- Change Map showed 30 readable second buttons and the six expected edit windows.
- Comparison loaded both original/revised players; shared playback started both, with observed time difference about 0.002 seconds.
- Keyboard slider navigation set both players to exactly 9 seconds and paused them together.
- Mobile stacked both players at 340px width with no horizontal page/dialog overflow.
- Escape closed the dialog and restored focus to `Compare this moment`.
- HNSW-default and QBit-requested library queries both returned the truthful empty-library state via MCP. The response explicitly said only count ran; actual engine remained exact, not a fabricated vector-search success. HNSW/QBit ranking and actual index selection remain proven by the isolated populated test, not by this empty production library.
- Public read-only save policy was visible; no private-key field or memory save action was enabled.
- Browser console: no errors during the tested flow. Initial revision warning query returned no rows.

Ignored evidence: `.gstack/live-intelligence-run-20260903.json` and `.gstack/design-reports/live-change-map-20260903.png`, `live-comparison-loaded-20260903.png`, `live-comparison-mobile-20260903.png`. Screenshots were visually inspected. The first immediate comparison screenshot showed the revised player before it finished loading; the later loaded screenshot and actual synchronized playback are the final evidence.

## Rollback and later removal

Previous serving revision: `revisionproof-staging-00014-r4l`. To restore only application traffic, after owner approval:

```bash
gcloud run services update-traffic revisionproof-staging \
  --project=revisionproof-agentic-2026-kan --region=us-central1 \
  --to-revisions=revisionproof-staging-00014-r4l=100
```

The extension schema is additive and need not be removed for application rollback. Alternatively redeploy with `_INTELLIGENCE_ENABLED=false`. Export before destructive removal. The exact seven objects and dependency order are inventoried in `qa-report-2026-09-03-clickhouse-intelligence.md`; shared roles, the database, existing data and historical backups must not be dropped. Cloud Shell archive/build directory and the new staging object are retained for traceability. Deleting any of them is a separate scoped cleanup action.
