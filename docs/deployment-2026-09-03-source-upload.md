# Source upload deployment — 2026-09-03

Status: **GitHub source push and Cloud Run deployment complete.** The owner explicitly approved Cloud Shell authorization, which was completed before the build. Revision `revisionproof-staging-00016-j4q` serves 100% of traffic.

## Source and verification

- Branch: `review/qa-hardening`, existing PRIVATE repository `devkan/RevisionProof`. No PR, merge or repository visibility change.
- Source commit: `d7676495ed7b2cf29a8ec03a9e865d9bb05f580c`. Push `c7ea226..d767649` succeeded and `git ls-remote` confirmed the exact SHA.
- Scope: original-video upload, explicit selection, actual-source A/B/full rendering, spec 2.1 full-video verification, optional lazy approved-memory references, and related documentation.
- Pre-release review reproduced final-frame failures at 4.01 and 6.01 seconds. Half-second midpoint sampling now omits only a codec tail shorter than 50 ms; real 4.01/6.01/4.04-second regression cases pass.
- Final backend regression: **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint, TypeScript/Vite production build and `git diff --check` passed.
- Committed-source archive: ignored `revisionproof-deploy-d767649.zip`, created with `git archive` from the source commit.
- Archive SHA-256: `b62ce8eb16cf0b5664560462ea14448d6f325e8343b7bf0345cb3a9f590da78d`.
- Secrets, source-upload test media, `.gstack/`, runtime files and foundation/live env files are excluded from Git and the committed archive.

## Verified deployment

The owner requested Git push and deployment, then explicitly approved the previously blocked Cloud Shell permission. The authorized session verified account `secureis@gmail.com`, project `revisionproof-agentic-2026-kan` / `348672234012`, and label `managed-by=revisionproof-gcp` before submitting the committed source. No global gcloud defaults were changed.

- Cloud Build: `41e73ed2-e824-485e-b464-e3fc166f259b`, **SUCCESS**, created `2026-09-03T07:25:32.176449758Z`, finished `2026-09-03T07:30:51.228859Z`. All four steps succeeded.
- Source staging object: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788420329.640306-80072ddcd420469784448199f3faf9f1.tgz`.
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:41e73ed2-e824-485e-b464-e3fc166f259b`.
- Image digest: `sha256:08a49f48e2684c0424c03fd340c7f7853f77572bf436f07fab4966dd0154938b`.
- Serving revision: `revisionproof-staging-00016-j4q`, **100% traffic**, Ready / ConfigurationsReady / RoutesReady all true.
- Public URL: [RevisionProof LIVE](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/).
- Rollback revision: `revisionproof-staging-00015-h6b`, preserved. Rolling back removes the upload feature and invalidates process-local run state; do not roll back without a concrete reason and owner authority.

Before deployment, a read-only guard checked the complete existing environment, two pinned ClickHouse secret references, runtime service account and resources. The release preserves 4 GiB / 2 CPU / concurrency 4 / service min-max 1, the runtime/build service accounts, ClickHouse host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`, and secret references `revisionproof-clickhouse-writer-password:1` / `revisionproof-clickhouse-mcp-password:1`. Memory remains public read-only. No ClickHouse migration or grant change was needed.

Fresh public `/health`, `/ready`, and `/api/runtime` returned **HTTP 200**. Runtime reports `LIVE`, `live_ready=true`, intelligence enabled, `memory_save_policy=read_only`, and upload limits `max_bytes=25165824`, `min_duration_seconds=4`, `max_duration_seconds=60`. `/ready` deliberately reports configured credentials, not successful integration execution; fresh per-run evidence is recorded below.

## Reproducible build input

The committed-source archive was transferred with an ignored release helper in `revisionproof-deploy-d767649-bundle.zip` (SHA-256 `ad39597e9dcc49693be860cf46978c5502a494af0504aa7dee658d96be8d01a7`). Both bundle and source hashes were verified in Cloud Shell. Source was extracted into the exclusive directory `/home/secureis/revisionproof-build-d767649`; the helper was outside that build source. The committed `cloudbuild.yaml` was submitted with:

```bash
gcloud builds submit \
  --async \
  --project=revisionproof-agentic-2026-kan \
  --config=cloudbuild.yaml \
  --gcs-source-staging-dir=gs://revisionproof-agentic-2026-kan-media/cloud-build-source \
  --substitutions=_CONFIRM_LIVE=YES,_REGION=us-central1,_SERVICE=revisionproof-staging,_REPOSITORY=revisionproof,_GCS_BUCKET=revisionproof-agentic-2026-kan-media,_CLICKHOUSE_HOST=r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud,_VERTEX_LOCATION=global,_GEMINI_MODEL=gemini-3.5-flash-lite,_WRITER_SECRET_VERSION=1,_MCP_SECRET_VERSION=1,_INTELLIGENCE_ENABLED=true \
  .
```

The Cloud Shell metadata directory `/home/secureis/revisionproof-release-d767649` contains the before/after service descriptions, build submission and final build status. Source archives, ignored local QA media, earlier Cloud resources, ClickHouse data/grants and backups were preserved. See [usage and implementation](source-upload-and-memory-ux-2026-09-03.md) and [preceding release](deployment-2026-09-03-clickhouse-intelligence.md).

## Fresh LIVE gstack verification

- Completed run: `01M1K3CSTV2R01X4VF3CHNFWK5`, started `2026-09-03T07:40:36.571811Z`. A desktop/browser interruption after the first upload interpretation required a fresh browser session; this completed run is separate from that interrupted attempt.
- Uploaded separate authored test media `portrait.mp4`: 12 seconds, 360×640, 3,210,193 bytes. The normalized source is 1280×720 H.264/AAC with aspect ratio preserved, and `source_kind=upload` / asset ID matches this run. The bundled sample was not used.
- Selected 2–8 seconds; LIVE interpreter `google.vertex.gemini`; evidence `user.selected_range`, blank transcript. A/B previews are 6 seconds at scales 1.05 / 1.12. Choosing B generated the complete original duration.
- Spec `2.1`, hash `31349d340a0c03c91faf6dd8130ddd5356d6865aa458e56f4caa387a12e06ab5`; the video and audio locks span 0–12 seconds.
- Final state **READY**, **three PASS checks**. Approved-patch similarity `0.9948`, five of five passing samples and winner margin `0.0297`; full-video preservation 24/24 samples; audio RMS delta `0.0 dB`. Matching MCP measurements are present in the raw proof.
- Change Map analysis `01M1K3H0C8XVZG4CJ2FWBMJJ63`, `source=mcp-clickhouse.run_query`, **12 windows / 24 samples / zero review flags**. Windows 2–7 are requested changes; 0–1 and 8–11 are unchanged. These are sampled diagnostics, not an every-frame guarantee. Rows were retrieved through the deployed official MCP path; no separate direct ClickHouse SQL inspection was performed for this release.
- Final delivery approval and memory save remain **false**. A/B choice is distinct from final delivery approval.
- Generated MP4: HTTP **200**, `video/mp4`, **1,571,345 bytes**, SHA-256 `9d02239efb590c21c783d033140bd6ac83443e5c760fb68c05f0aa5d4f57d3cf`. Downloaded-file FFprobe verifies **12.000000 seconds**, 1280×720, H.264/AAC. Browser playback completed to 12 seconds with `ended=true` and no media error.
- 25 MiB upload produced an actual-size / 24 MiB warning; 61-second upload produced a 4–60-second warning. No run upload requests were sent for those rejected selections.
- `Past approved edits` starts collapsed and made **zero memory requests before expansion**. Opening it returned `status=empty`, collection size `0`, `actual_engine=none`, source `mcp-clickhouse.run_query`. The UI displays public read-only guidance and has no search buttons or engine selector in this empty state.
- Mobile viewport 390×844: document width 390, no horizontal overflow. Desktop 1280×900 and mobile captures were visually inspected. No console errors or recorded resource responses >=400 in the completed browser session.

Ignored local evidence: `.gstack/source-upload-live-proof-20260903.json`, `.gstack/source-upload-live-generated-20260903.mp4`, `.gstack/source-upload-live-ready-20260903.png`, `.gstack/source-upload-live-memory-mobile-20260903.png`. These are not published in Git. Run state and normalized originals are process-local; a service restart can make the run API unavailable even though generated media/evidence persistence is separate.

## Follow-up scope

The requested upload/UX release is complete. Enabling approved-memory writes requires separate owner-key setup; automatic transcription/scene indexing, durable original storage and run restoration remain outside this release. Final deployment documentation is committed separately from deployed source `d767649` and does not require another build.
