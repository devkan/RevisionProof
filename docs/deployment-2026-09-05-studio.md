# Studio LIVE deployment and hands-on QA

Date: 2026-09-05 KST. Status: **push, deployment, corrective LIVE QA and final canary complete**.

## Final copy follow-up

- Source `44cc8c0a4f4d1c8cb4fa66badc9aa96b3e14bcac`, pushed. Exactly one JSX line changed after the successful functional QA: the final Applied summary also uses the tested singular/plural helper (`1 edit`). No workflow or backend changes.
- Full frontend tests repeated: **51 PASS / 12 files**, lint and build PASS. Final expected bundle `index-BmgsfeTd.js`.
- Archive SHA-256 `0e0b3db27c57c800699a24e8fea45e0fa06f7e7e8b109e18d587949cd5a020ab`, independently verified in Cloud Shell; new directory `/tmp/revisionproof-deploy-44cc8c0.JTEOIN`.
- Build `660dbd2f-1bf5-4ab1-9cb1-59c41277b340`: **SUCCESS**, unchanged pinned configuration. Created `2026-09-05T09:41:06.699694802Z`, finished `2026-09-05T09:49:03.699799Z`.
- Final image `sha256:344c7256c2d1a68db5a2c23d3a229e869f02f488332bda5fd49aeb12b7c7e36a`.
- Final served revision **`revisionproof-staging-00028-n4z`**, **100% traffic**; Ready, ConfigurationsReady and RoutesReady True. Ready transition `2026-09-05T09:49:00.994771Z`.
- Browser confirmed final `index-BmgsfeTd.js`; `/health`, `/ready`, `/api/runtime` returned 200 with the preserved LIVE configuration. Fresh source selection, edit tool and plan creation worked. The final one-line Applied count was verified in local full run `01M1RF5761Z6Q9D1XQPXDC7171`; full LIVE functional rendering/verification evidence remains the immediately preceding 00026/00027 runs below, not a claim that every full run was repeated after a text-only change.
- Final canary run `01M1RFPEN1BG17X6MZQ8B0ZF6V` accepted the sample cut plan. Opening Approved edits and its optional reference section completed successfully with `No saved edits yet`; saving remains disabled. Fresh post-fix console has no errors. JSON evidence: `runtime/qa-screenshots/studio-final-canary-run-20260905.json`.

## Functional corrective release (preceding final copy follow-up)

- Source `3ca72e49772fa66ad1ebd66e7e38daa52f32051e`, pushed to the same private branch. Includes upload preparation fix `ab5a6b8` and single-preview copy fix `3ca72e4`.
- Archive SHA-256 `0d1b5ba331846afed84ef83f0ae53663c2947db35ec9ba7685ea5cdc439809d3`, independently verified in Cloud Shell before extraction to `/tmp/revisionproof-deploy-3ca72e4.7Rdwxq`.
- Cloud Build `43ba819f-5486-42e3-9574-1967462c2410`: **SUCCESS**, all four steps successful. Created `2026-09-05T09:22:02.122951626Z`, finished `2026-09-05T09:28:40.318787Z`. Same explicit project, service, region, model, bucket, service accounts and pinned secrets as the initial deployment.
- Image `sha256:6a75137c46150d932cf60ea112a20770494e2137e958703559857db00e6b7608`.
- Served revision **`revisionproof-staging-00027-rs2`**, **100% traffic**; Ready, ConfigurationsReady and RoutesReady all True. Ready transition `2026-09-05T09:28:37.613455Z`.
- Actual browser loaded `index-3flB8rGc.js` from the LIVE service. `/health`, `/ready` and `/api/runtime` all returned 200; LIVE mode, no missing settings, intelligence enabled, 32,000,000-byte upload limit, read-only memory. Readiness explicitly reports `integration_execution_verified=false`; successful integration execution is proven by the QA runs, not this configuration response alone.
- Final-source frontend: **51 tests in 12 files PASS**, ESLint PASS, TypeScript/Vite build PASS, `git diff --check` PASS. Expected JS `index-3flB8rGc.js`, CSS remains `index-BTRL_Fp0.css`.
- Backend unchanged from the 349-test run below. Windows sandbox initially blocked Vite child processes with `spawn EPERM`; the identical commands passed when rerun with approved normal process permissions.
- Local synthetic upload → four unchecked silence suggestions → one selected cut → one A preview → full-video checks reached PASS / 3 of 3. Single-preview heading, hint, action and singular counts were visually verified. After screenshot: `runtime/qa-screenshots/studio-local-single-preview-fixed-20260905.png`.
- Scoped review of both fixes found no additional actionable issue. Full edit plan, scene IDs, frozen spec, server validation and final-delivery gate remain unchanged. No CSS, classic page, backend, CI, schema or infrastructure edits.

## Release identity

- Source: `0dfa8f3a6be1ed65479b105ac6431cb81caf0812`, pushed to `origin/review/qa-hardening` in the existing private repository. No PR merge, force-push, branch deletion, or visibility change.
- Target: `revisionproof-staging`, project `revisionproof-agentic-2026-kan` / `348672234012`, `us-central1`, existing account `secureis@gmail.com`.
- User completed the Cloud Shell authorization gate. The disconnected shell was reconnected, then the active account and project identity were verified before deployment.
- Source archive SHA-256: `a5848450b2db5747bab4a9d280e85d2bb973df35958450e1866bc26ab49ba5dd`. Cloud Shell independently verified the checksum before extraction into a new temporary directory.
- Build: `08642b5a-3da7-426f-ab22-1e2b52feb5e6`, SUCCESS. Created `2026-09-05T08:31:02.085281168Z`; finished `2026-09-05T08:37:12.625564Z`.
- Image: `sha256:b4f168d45ad106a7f850a8b94400fe18d1e85c90b24d395d8bf94960f8787ef5`.
- Revision: `revisionproof-staging-00026-l4c`, traffic **100%**. Ready, ConfigurationsReady, and RoutesReady all True at the post-deploy check.
- Browser loaded the expected `index-DRghn6Mr.js` bundle at `/studio?release=0dfa8f3`.
- [LIVE Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) remains separate from [Classic UI](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/).

## Preservation and rollback

- Pre-Studio healthy LIVE revision: `revisionproof-staging-00025-88t`, confirmed at 100% before deployment and retained as the classic rollback target. Functional Studio revision `revisionproof-staging-00027-rs2` is also retained; it has only the final-summary plural typo compared with 00028.
- Pushed source backups: `backup/pre-studio-ui-20260904` at `270d37db02c8b05f99068778066140cc9e34eadd`; `backup/pre-studio-reqa-20260905` at `ca87a0593e78278a761c1239fd6427ca50f2e356`.
- Preserve the active worktree. Inspect old source by creating a separate worktree from either backup, not by resetting the current branch.
- An explicitly approved emergency traffic rollback can use:

```sh
gcloud run services update-traffic revisionproof-staging \
  --project=revisionproof-agentic-2026-kan --region=us-central1 \
  --to-revisions=revisionproof-staging-00025-88t=100
```

This rollback command is documented, not executed. It restores the previous classic release and removes Studio from served traffic until redeployed.

Existing runtime/build service accounts, 2 CPU / 4 GiB, concurrency 4, min/max 1, Google model/location, media bucket, ClickHouse host and secret references pinned to version 1 were preserved. No credential values were read. No migration, grant, billing, or global gcloud default was changed. Public Approved Edit Memory stays read-only.

## Exact-source checks

- Backend: **349 passed in 145.63s**. One non-fatal Windows pytest cache-write warning; no test failures. New isolated test directory: `runtime/pytest-deploy-20260905`.
- Frontend: **29 passed in 10 files**. ESLint passed.
- Ruff check passed; 69 Python files already formatted.
- Production frontend build passed in the previous exact-source local QA and again within this successful Cloud Build.
- This branch does not trigger the repository's main/PR-only GitHub Actions workflow. These are local and Cloud Build results, not a claim of GitHub Actions success.

## LIVE QA evidence

The gstack headless browser tests the deployed service, not the local FIXTURE server. The existing synthetic Korean/English video is used: `runtime/qa-inputs/mixed-speech-demo.mp4`, SHA-256 `f1fcad67d09a997fee5403ca677342bd9f224b8384dfc3537aba6c1749377fdb`, 9,983,200 bytes. No private source movie is retransmitted.

Scoped QA is complete. Final delivery approval and Approved Edit Memory writes are outside this test boundary and remained untouched. See [the QA report](qa-live-2026-09-05-studio.md) for scope, score and limitations.

### Confirmed workflows on revision 00026

- Run `01M1RBSCTZ53VSRWKCZ6MTG9YJ`: synthetic source upload; three reviewed/corrected mixed-language speech captions, 1.5x speed on 0–8s, -6 dB on 0–8s, full-video logo. B reached READY / 3 PASS. Prepared 9.93s became 7.266667s. Spec hash `f95c7005519fa084979ae971985b3ed1765ef9acc9693ff3c731b0167bb29bb2`; Change Map source `mcp-clickhouse.run_query`, zero residual flags. Original/result synchronized playback worked; both players readyState 4 and playing. Delivery approval false.
- Speech transcription returned four cues on the first test and three on the second; generated product spelling `KANEB` was corrected to `KANAPP` before the final plan. Template selection explicitly replaces the list; speech generation adds/replaces captions while preserving other tool types.
- At 390x844, document width was 390, approval button bottom 837, and footer font Manrope. Public memory returned an empty, read-only library and no save control.
- Smart scene search indexed eight sample segments, returned three results, and carried the chosen 16–20s range into an editable zoom draft. Search 200 / 14.299s; interpretation 200 / 2.062s.
- Run `01M1RC9PX405X5CXVAHNPSRW2K`: smart-scene zoom, exact text, manual timed caption and 0–0.5s cut. A/B generated; returning to Plan preserved the frozen selection and offered Continue to previews without creating another run. An unchanged 30s file was correctly rejected with 409 because this plan requires 29.5s, leaving external retry available.

### ISSUE-LIVE-001: first edit range incorrectly controls source preparation

- Severity: High, functional. Reproduced twice on the deployed Studio.
- Repro: upload the 9.962s synthetic speech video; add only Remove silence (default full-video range); press Check plan.
- Actual: POST `/api/runs/upload` returns 422, `Select a 4–8 second section to edit.` No run is created. Screenshot: `runtime/qa-screenshots/studio-live-silence-error-20260905.png`.
- Root cause: Studio passes the first operation range as the legacy source-preparation range. Full-video silence/overlay edits exceed 8s; short captions/cuts can be below 4s. The existing classic guided flow uses a separate bounded preparation range.
- Correction scope: Studio upload request construction and regression tests only. Preserve the full edit plan, source timeline, explicit scene IDs, classic page, and backend validation.
- Fix: `ab5a6b8`; separates the bounded preparation anchor from the full edit plan. Sixteen regression cases added. Verified locally and LIVE on revision 00027: four silence candidates, all initially unchecked, one chosen cut rendered and full checks PASS. Final frontend suite now 51 tests.

### ISSUE-LIVE-002: single preview is described as an A/B pair

- Severity: Medium, UX/content. Reproduced on the cut-only local follow-up after ISSUE-LIVE-001 was fixed; the same hard-coded copy is deployed in revision 00026.
- Repro: select one suggested silence cut and create previews. The backend correctly returns only A, but the heading/footer instruct the user to compare both versions and choose A or B. Counts also read `1 items`, `1 versions`, and `1 revisions`.
- Before: `runtime/qa-screenshots/studio-local-single-preview-before-20260905.png`.
- Correction: match instructions to the candidate count and singularize count labels. Keep the existing layout and two-candidate guidance.
- `3ca72e4` verified locally and LIVE with one A preview and correct single-version instructions. Final approval-summary count required one additional JSX line (`44cc8c0`), using the same tested helper.

### Confirmed post-fix LIVE workflows on revision 00027

- Run `01M1REEYNYAKDJ2EF1KPCRRE4F`: exact former failure path, 9.962s synthetic source with whole-video Remove silence, returned four suggestions. All unchecked; Create previews disabled until one was selected. Only 1.1–1.8s was selected, yielding one A preview, then READY / **3 PASS** with 9.233333s output.
- Spec `d8fb37b8b6783ab2447b63dc3f2f94a1afcfbfd17e30b12597187711e64a1a57`; Change Map source `mcp-clickhouse.run_query`, all residual deltas zero. Proof generated `2026-09-05T09:35:34.474339Z`. Result video readyState 4, no media error, delivery approval false. Persisted JSON: `runtime/qa-screenshots/studio-live-silence-ready-run-20260905.json`.
- Run `01M1REMECEG9K0XRQGYDJ3ZC6H`: uploaded source with only a 0–2s caption, `A clear, short caption.` Plan accepted and original caption range retained. This verifies the short-range side of the same upload bug; no full render claimed for this focused probe. JSON: `studio-live-short-caption-run-20260905.json`.
- Browser widths 320, 390, 768 had matching document widths and CTA bottoms 733/837/1017 within 740/844/1024 heights. 1280px retained the three-column layout. Result playback reached readyState 4 at 390px with Manrope. Classic UI link was clicked and loaded the preserved original page.
- gstack automation initially selected a file before one new tab finished initialization; the disabled source picker intentionally ignored it. Retrying after readiness succeeded. Some over-specific text selectors also timed out; fresh observed accessibility references worked. These are harness timing/selector retries, not API failures.

### External edit recovery completed

- In run `01M1RC9PX405X5CXVAHNPSRW2K`, a duration-matched 29.5s negative file containing only the cut was BLOCKED: approved patch and protected CTA failed, locked audio passed, five Change Map flags. Approval remained locked.
- Uploading the exact selected A preview as the corrected external file then reached READY / 3 PASS. `generated_version_url` is null, proving this was external-file verification, and `delivery_approved` stayed false.
- Evidence: `runtime/qa-screenshots/studio-live-external-corrected-run-20260905.json` and `studio-live-external-corrected-20260905.png`.
