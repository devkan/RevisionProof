# English request-form examples

Status: **DEPLOYED AND VERIFIED**, 2026-09-06 KST.

## Scope and source

- User requested English placeholders, then immediate push and deployment.
- Source: `f18570fb897abb1d959137269b9dd51cb484c8ef`, pushed to `review/qa-hardening` in the existing repository. No PR, merge, force push, or visibility change.
- Shared `RequestDraft` in `frontend/src/EditComposer.tsx` serves both Studio and classic UI.
- Scene search example: `e.g., a close-up of the dashboard chart`.
- Edit request example: `Zoom in from 4 to 10 seconds and show "AI, made practical." at the bottom.`
- Matching time guidance now uses `4–10 seconds`.
- No layout, handlers, API contracts, user-entered text, or Korean-language input support changed.

## Verification

- Regression reproduced before the fix: 1 failed / 2 passed. The failure showed the previous Korean placeholder.
- After the fix: frontend **72 passed / 15 files**; ESLint and TypeScript/Vite production build passed; `git diff --check` clean.
- Regression coverage checks empty-form English copy and preserves enabled request submission for both English and Korean explicit time ranges.
- Browser bundle: `index-BYBHYv_J.js`; unchanged CSS: `index-BaYy-LUs.css`.
- No backend changes; backend suite and paid provider/render workflows were not rerun for this copy-only patch. Hosted GitHub CI does not trigger for this branch push.
- The previous local server at port 18131 is not running; no user draft was reloaded or reset. Final checks used separate LIVE browser tabs.

## Final LIVE verification

- Cloud Build `af06b685-03a4-4f85-9629-b7d4591e0c0b`: **SUCCESS**, all four steps successful; start `2026-09-06T04:31:18.449602853Z`, finish `2026-09-06T04:37:22.219361Z` (about 6 minutes).
- Image digest: `sha256:360249dc5a27a114261c844215bd84a6daaa73dc40676d3a60062edc5430f294`.
- New revision `revisionproof-staging-00030-gnz` receives **100% traffic**. Ready, ConfigurationsReady and RoutesReady are all True.
- [LIVE Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) loads `index-BYBHYv_J.js`, matching the verified local build.
- `/health`, `/ready`, `/api/runtime`: HTTP **200**; LIVE, no missing settings, 32,000,000-byte source limit, intelligence enabled, memory `read_only`. `integration_execution_verified=false` remains an explicit configuration-versus-execution boundary.
- Selected the authored sample in a separate Studio tab, entered Edits, and inspected the request placeholder and English time hint.
- Entered the new English request example: time recognized and `Turn request into edit plan` enabled. A Korean `4–10초` request was also recognized. Clearing through a normal Backspace keystroke restored the English placeholder and disabled the empty-request action.
- Enabled Smart scene finder and verified `e.g., a close-up of the dashboard chart` in the scene input. The cost disclosure remains visible; no search or interpretation was submitted.
- [Classic UI](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/) independently displayed both English placeholders, including the conditional scene-search field.
- No captured browser warnings or errors in either LIVE tab. Two Studio screenshots were captured and visually inspected inline in the task; no standalone screenshot file is claimed.
- Classic navigation took 884 ms at the automation-call boundary. This is not a browser Navigation Timing / Web Vitals measurement. The browser's read-only evaluation scope did not expose `performance`; no fabricated browser timing is reported.
- The automation's empty-string fill initially selected existing text without deleting it. The displayed value exposed this tool behavior; a normal Backspace cleared it successfully. No application code change was needed.
- No media upload, paid Gemini/ClickHouse request, video render, final approval, or memory write was performed. This was a copy/interaction canary, not a fresh full editor E2E run.

## Deployment and recovery

- Target: project `revisionproof-agentic-2026-kan` / `348672234012`, service `revisionproof-staging`, region `us-central1`, existing account `secureis@gmail.com`.
- Predeploy read-only check: project label `managed-by=revisionproof-gcp`; revision `revisionproof-staging-00029-2t2` Ready at 100% traffic.
- Preserved source backup: `backup/pre-english-placeholders-20260906` at `05983f3169379087dfb5970fc733b88bc7acff1f`, pushed and remote-verified. Existing backups remain intact.
- Predeploy service export: `/home/secureis/revisionproof-before-english-f18570f.yaml`, private and outside Git.
- Source ZIP: local ignored `runtime/revisionproof-deploy-f18570f.zip` and Cloud Shell `/home/secureis/revisionproof-deploy-f18570f.zip`; 568,294 bytes; SHA-256 `662365923528593030af7406a34e9afad52109f46f60be60e90177fad971755c`, verified at both ends.
- Extracted committed source: `/tmp/revisionproof-deploy-f18570f.mlfWpy`.
- First submission omitted the explicit staging directory and failed source resolution with HTTP 403 before build execution. Its uploaded source object is `gs://revisionproof-agentic-2026-kan_cloudbuild/source/1788669011.742645-0de61d6046aa45ba965d9fd42c1a65ce.tgz`; no deletion or IAM changes performed.
- Corrected submission uses the existing documented `--gcs-source-staging-dir=gs://revisionproof-agentic-2026-kan-media/cloud-build-source`, as in `infra/gcp/deploy-live.sh`. Preserve this flag on future submissions.
- Successful build source object: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788669074.371752-787a7df47c4547fa8f7ae81477288644.tgz`.
- Existing `cloudbuild.yaml`, runtime/build service accounts, resource limits, model `gemini-3.5-flash-lite`, global Vertex location, ClickHouse host, intelligence flag, bucket, and pinned secret versions 1/1 are unchanged. No secret values inspected.
- gstack `land-and-deploy` is adapted to this established direct Cloud Build workflow, without its PR/merge steps. Browser checks use the connected browser automation surface.

Rollback target is `revisionproof-staging-00029-2t2`. No rollback executed. Run state is process-local; restoring a revision does not recover old in-memory runs. No final delivery approval or Approved Edit Memory write is part of this task.

Documentation committed after deployment does not change the deployed source identity `f18570f`. This Codex-authored copy patch is not a Google-tool rewrite or an eligibility determination.
