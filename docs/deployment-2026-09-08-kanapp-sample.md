# KANAPP sample video deployment

Date: 2026-09-08 KST. Status: deployed and verified.

## Change

**Use sample video** now loads the owner's exact
`kanapp_promo_english_editable_30s.mp4` used in the published walkthrough.
It is bundled with the application, so judges do not need to upload a file.
See the [sample provenance and checksum](../assets/demo/README.md).

- Studio and the classic video editor default to KANAPP.
- The original scene-search proof demo retains its Product Reveal clip, asset ID,
  and scene index. KANAPP cannot accidentally use that unrelated legacy index.
- Sample selection resets source-bound drafts. Each planned run owns an immutable
  copy of the selected source for preview and export verification.
- Public media serving allows the exact sample filename and supports HTTP ranges.

## Source and CI

- [PR #3](https://github.com/devkan/RevisionProof/pull/3), normal merge into `main`.
- Implementation: `621423b5168b953eb8cc9ec6074bc28303e4397b`.
- Main merge: `a0c589ba10a241722f6301dec68e365041039249`.
- The deployed archive is from `621423b`; its tree was verified identical to the
  merged `main` tree. Later documentation-only commits do not alter this deployment.
- Archive SHA-256: `c59c22ac8bc7271406834a30ca29473fe7903e5d5e4fa8beacac24a1f1862743`.
- [PR CI](https://github.com/devkan/RevisionProof/actions/runs/34192901566) and
  [merged-main CI](https://github.com/devkan/RevisionProof/actions/runs/34193827470):
  SUCCESS, including quality/container build and isolated ClickHouse integration.
- Local checks: 357 backend tests, 82 frontend tests, Ruff lint/format, frontend
  lint/build, demo packaging, full MP4 decode, and `git diff --check` passed.
  Backend coverage includes sample preview, approval, and verified export.

## Deployment

- Existing GCP project: `revisionproof-agentic-2026-kan`; region: `us-central1`.
- [Cloud Build](https://console.cloud.google.com/cloud-build/builds;region=us-central1/1bc66b0f-a094-4f84-8215-925b518b867b?project=348672234012):
  `1bc66b0f-a094-4f84-8215-925b518b867b`, SUCCESS at `2026-09-08T06:25:44Z`.
- Active revision: `revisionproof-staging-00032-np7`, ready and serving 100% traffic.
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:1bc66b0f-a094-4f84-8215-925b518b867b`.
- Image digest: `sha256:35fdf403d0b52e068e9babbf8f1a5c05d9153a6abda7404ea21098575cc080e0`.
- Rollback reference: `revisionproof-staging-00031-5bl`; no rollback performed.
- Before/after service comparison confirmed unchanged runtime settings, container
  configuration apart from the image, environment/secret references, and scaling.
  CPU 2, memory 4 GiB, concurrency 4, min/max 1, Gemini model/location, and
  read-only public memory policy remain unchanged. No migrations or grant changes.
- Private Cloud Shell evidence is retained under
  `/home/secureis/revisionproof-release-20260908-kanapp/` (`before.json`, `after.json`,
  `build-submitted.json`, `build-final.json`, and the extracted source).

## Public smoke test

On the [live Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio):

- Clicking **Use sample video** loaded KANAPP, 30 seconds, 1280 x 720, H.264/AAC.
  Browser playback advanced with no media error; console error count was zero.
- Downloaded sample SHA-256 exactly matched the supplied original:
  `ce6270bbd3eac7359d173fa34386b8f00ab1bc83c571e0c9bb27e030003d4d91`.
- Range request returned HTTP 206; `/health` and `/ready` returned HTTP 200 / LIVE.
- Studio HTML returned HTTP 200 in a 239 ms request measurement (not a full browser
  performance benchmark). Both rendered preview files returned HTTP 206 / video/mp4.
- Separate QA run `01M1ZV6NGH6HQGXT4T0G1G6365` reviewed a 4–8 second zoom and generated
  A/B previews, reaching `PREVIEWS_READY`. Final delivery approval remained false;
  no public memory entry was saved.
- This smoke test exercised media serving and planned preview rendering. It does
  not claim a new Gemini/MCP call or final human delivery approval.

Runs are process-local and may expire; the recorded observation is historical
evidence, not a promise that this QA run remains retrievable indefinitely.
