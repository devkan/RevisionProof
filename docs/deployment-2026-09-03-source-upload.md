# Source upload release preparation — 2026-09-03

Status: **GitHub push complete; deployment awaits Cloud Shell authorization.** No Cloud Build was submitted and no Cloud Run revision was created during this attempt.

## Source and verification

- Branch: `review/qa-hardening`, existing PRIVATE repository `devkan/RevisionProof`. No PR, merge or repository visibility change.
- Source commit: `d7676495ed7b2cf29a8ec03a9e865d9bb05f580c`. Push `c7ea226..d767649` succeeded and `git ls-remote` confirmed the exact SHA.
- Scope: original-video upload, explicit selection, actual-source A/B/full rendering, spec 2.1 full-video verification, optional lazy approved-memory references, and related documentation.
- Pre-release review reproduced final-frame failures at 4.01 and 6.01 seconds. Half-second midpoint sampling now omits only a codec tail shorter than 50 ms; real 4.01/6.01/4.04-second regression cases pass.
- Final backend regression: **292 passed in 101.74s**; frontend **19 passed**; Ruff check/format, ESLint, TypeScript/Vite production build and `git diff --check` passed.
- Committed-source archive: ignored `revisionproof-deploy-d767649.zip`, created with `git archive` from the source commit.
- Archive SHA-256: `b62ce8eb16cf0b5664560462ea14448d6f325e8343b7bf0345cb3a9f590da78d`.
- Secrets, source-upload test media, `.gstack/`, runtime files and foundation/live env files are excluded from Git and the committed archive.

## Verified target and authorization block

The owner requested Git push and deployment. The in-app Google Cloud console was opened using the existing `secureis@gmail.com` account, and showed project `revisionproof-agentic-2026-kan` / `348672234012`. Cloud Shell opened under `secureis` with that project.

Cloud Shell displayed its `Authorize` dialog to use the existing Google credentials for current and future API calls. Automatic approval review rejected the Authorize click because it viewed that ongoing credential use as a security-sensitive permission whose scope was not specifically authorized. The rejected action was not bypassed. A question requesting explicit approval for this exact permission was sent to the owner; no affirmative response had arrived when this record was written.

The authorization tab remains available in the in-app browser. Continue after the owner explicitly approves this Cloud Shell permission or completes the Authorize action themselves. Do not substitute a credential-export or indirect execution workaround for the rejected action.

Fresh public `/api/runtime` check still reported `LIVE`, `live_ready=true`, intelligence enabled, `memory_save_policy=read_only`, and no new `upload_limits` field. This confirms the upload feature is not yet on the public service. Revision `revisionproof-staging-00015-h6b` is the last recorded deployment; it was not re-read through a newly authorized Cloud API session in this attempt.

## Remaining deployment steps

1. Complete the explicit Cloud Shell authorization above. Recheck active account `secureis@gmail.com`, project number and `managed-by=revisionproof-gcp` label, and current Cloud Run configuration.
2. Upload the committed archive to Cloud Shell, verify its SHA-256, and extract into an exclusively created directory such as `/home/secureis/revisionproof-build-d767649`. Preserve earlier archives and directories.
3. Verify the current host and pinned secret references match the existing deployment, with no newly configured memory token to overwrite. Then submit the committed `cloudbuild.yaml` with the existing substitutions below. No ClickHouse migration is needed.

```bash
gcloud builds submit \
  --async \
  --project=revisionproof-agentic-2026-kan \
  --config=cloudbuild.yaml \
  --gcs-source-staging-dir=gs://revisionproof-agentic-2026-kan-media/cloud-build-source \
  --substitutions=_CONFIRM_LIVE=YES,_REGION=us-central1,_SERVICE=revisionproof-staging,_REPOSITORY=revisionproof,_GCS_BUCKET=revisionproof-agentic-2026-kan-media,_CLICKHOUSE_HOST=r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud,_VERTEX_LOCATION=global,_GEMINI_MODEL=gemini-3.5-flash-lite,_WRITER_SECRET_VERSION=1,_MCP_SECRET_VERSION=1,_INTELLIGENCE_ENABLED=true \
  .
```

4. Verify Cloud Build success, image digest, serving revision and traffic. Preserve 4 GiB / 2 CPU / concurrency 4 / min-max 1, runtime/build service accounts and pinned secret bindings. Do not change global gcloud defaults.
5. Use gstack on the LIVE URL to upload a separate video, select a 4–8-second range, generate A/B, choose B, and verify full-video playback/download, three PASS checks and an MCP-backed Change Map. Check zero-record memory returns `actual_engine=none`, plus size/duration warnings. Do not grant final delivery approval or save a memory record on the owner's behalf.
6. Record fresh build/image/revision/run IDs and evidence, update this file and HANDOFF, and push the final deployment documentation.

Existing local FIXTURE instances at 18125/18126, Cloud resources, ClickHouse data/grants and backups were preserved. See [usage and implementation](source-upload-and-memory-ux-2026-09-03.md) and [preceding release](deployment-2026-09-03-clickhouse-intelligence.md).
