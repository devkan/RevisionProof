# KANAPP demo upload: audio and request review fixes

Date: 2026-09-03. This follow-up fixes the failures reported with `614.png` and `demo_movie_kanapp.mp4`. Text/caption/logo insertion is still not implemented; the earlier conversation's compound-edit example described a possible extension, not an available feature.

## Reproduced causes

- Original file: `../video/demo_movie_kanapp.mp4`, 2,052,522 bytes, 1280×720 H.264 at 24 fps, AAC, duration 10.005 seconds. QA uses an ignored copy and preserves the original.
- Uploading it and choosing B for 4–10 seconds produced a local BLOCKED proof despite the patch and full-video checks passing. Source and candidate RMS were both `-12.65 dBFS`; their decoded audio peaks were both `+1.01 dBFS`. The old upload spec's absolute 0 dBFS ceiling rejected the unchanged source audio. This was not an audio change caused by the edit.
- Exact compound feedback `4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시` reproduced LIVE failure in run `01M1K67R91TJSCW4PB2Z0QSX35`. Authorized Cloud Run logs showed `RuntimeError: Gemini returned a target phrase absent from its source note`. Uploaded timing was already selected by the user, but a model-produced phrase was unnecessarily used as a grounding requirement. Without quotes a separate run returned a clarification question about unsupported text styling, another misleading outcome.
- The text field was disabled once a run existed, and a failed run only offered retry. There was no nearby way to edit the unsupported request while keeping the video and selected section.

## Changes

- New uploaded proofs freeze spec **2.2**: audio RMS delta <=3 dB and absolute peak delta from the prepared original <=0.1 dB. Both local verification and the official MCP feature-diff recomputation use the same rule. Existing 2.0/2.1 specifications retain their original absolute ceilings and hashes. Check IDs and ClickHouse feature rows stay unchanged; no migration is needed.
- Uploaded notes use a verbatim source-language label, with the user's explicit range as timing evidence. Exact input-note coverage validation remains active. Sample-video phrase searching remains unchanged.
- Known text/caption/logo or other unsupported requests are held as whole manual notes in LIVE and FIXTURE. A compound request never silently executes only its zoom part. The model prompt now explicitly states this boundary.
- The screen states that only center punch-in is supported. `Edit request` keeps the local file selection, range and wording, lets the user edit them, and submits a new review. Retry still exists for transient failures. Failed reviews no longer show a completed status/check icon, and the blocked message no longer asserts a change when a check merely failed.

## Verification

- Before fixes, regressions reproduced both the high-peak false block and uploaded Korean target mismatch.
- Backend: **303 passed in 102.14s**. Frontend: **19 passed**. Ruff check/format, ESLint, production build and `git diff --check` passed.
- Synthetic high-peak AAC upload passes when audio is unchanged. Adding 1 dB fails local verification even though RMS delta is under 3 dB. MCP recomputation separately passes equal positive peaks and rejects a changed peak. Invalid/overbroad relative tolerances and positive legacy ceilings are rejected.
- gstack local server: `http://127.0.0.1:18127`. The exact compound request displays one manual note; `Edit request` restores editable text with the file and 4–10-second selection intact.
- Local browser run `01M1K6VB9HVFPY112AQRKXD9EC` then used `선택한 4–10초 구간을 중앙 기준으로 확대해 주세요.` and Option B on the same actual KANAPP file. **READY / three PASS / zero Change Map review flags**, spec 2.2, RMS and peak deltas both 0. Source/candidate peak remains +1.01 dBFS. No final delivery approval was granted. Evidence: `.gstack/kanapp-debug-after-browser.json`.
- Ignored evidence: `.gstack/kanapp-debug-before.json`, `.gstack/kanapp-live-failed-614.json`, `.gstack/kanapp-debug-runtime/`, `.gstack/kanapp-debug-browser/`. Cloud Shell log excerpt is in `/home/secureis/rp-debug-614.log`.

## Deployment

- Application source `1c1204620382244fc817ce4f8f457f6867dc57cc` was pushed to the PRIVATE repository's `review/qa-hardening` branch. Post-deployment documentation is a later commit.
- SHA-256 of the committed-source archive: `e9b2424608cd41581ab327b98fbe4d37c9f5fc48a8ecf86def966a0434501433`. Transfer bundle SHA-256: `31b70561485d9508e41b2ecce2da31d7947427bb63859db35081e4c77031fd0c`. Both exclude ignored media, QA evidence and credentials.
- Cloud Build `95808615-6694-4d67-ad58-c04097cbf46a`: **SUCCESS**, finished `2026-09-03T08:51:17.608781Z`.
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:95808615-6694-4d67-ad58-c04097cbf46a`; digest `sha256:ad118dc715b9bdbbb4489ce523581f3ccbbc1efcbd93c26b67edf02b9869a5c2`.
- Revision `revisionproof-staging-00017-cnr`: all three Cloud Run readiness conditions True, **100% traffic**. `/health`, `/ready`, `/api/runtime` returned HTTP 200. The existing account/project, pinned ClickHouse secret versions, read-only memory, 4 GiB / 2 CPU / concurrency 4 / min-max 1 were preserved. No migration or resource deletion was performed.
- Cloud Shell evidence: `/home/secureis/revisionproof-release-1c12046/build-status.json` and `service-after.json`. Source/extraction/helper files remain available; no cleanup was performed.

## Fresh LIVE checks and approval boundary

The actual KANAPP file passed the local checks above. Automatic approval review rejected retransmitting that file to LIVE after deployment because it required explicit approval for the file and exact destination. The real file was not retransmitted after that rejection. The browser's local file-selection step was separately cleared by review after confirming it only reads local metadata; the subsequent network-upload step remained rejected.

To complete unaffected LIVE QA, FFmpeg generated a separate 10-second test-pattern/sine-wave video with intentionally high decoded AAC peaks. This file contains no company footage: `.gstack/upload-inputs/generated-high-peak-10s.mp4`, SHA-256 `3c978186e3088203241d690048e7180a0521cfdd2c9ae4550397ba82dc565782`.

- Exact compound Korean feedback now produces one manual note and no FAILED state. Fresh-UI run `01M1K7W9763JK70AV2NGBDTTHJ` shows supported-edit guidance and `Edit request`. Clicking it preserves the exact curly-quoted wording and 4–10-second selection in an editable form. Evidence: `.gstack/kanapp-fix-live-synthetic-manual.json`, `.gstack/kanapp-fix-live-manual.png`.
- After editing to `선택한 4–10초 구간을 중앙 기준으로 확대해 주세요.`, run `01M1K7XV7QF85PVHE9Q1EKD9HQ` used LIVE Gemini, generated A/B, and applied B to the full 10-second synthetic original. **READY / three PASS**, spec 2.2, at `2026-09-03T09:02:44.002101Z`. Official MCP recomputation reports source and candidate peaks both **+2.13 dBFS**, RMS both **-3.69 dBFS**, and both deltas **0**. Change Map: `mcp-clickhouse.run_query`, 10 windows / 20 samples, zero review flags. Final delivery approval and memory save remain false.
- The generated MP4 downloaded successfully: H.264/AAC, 1280×720, 10 seconds, 2,540,134 bytes. Browser playback advanced past 4 seconds with no media error. At 390px the page width is 390px; console errors and resource responses >=400 were absent. Evidence: `.gstack/kanapp-fix-live-synthetic-ready.json`, `.gstack/kanapp-fix-live-synthetic-final.mp4`, `.gstack/kanapp-fix-live-ready.png`.
- The existing browser initially reused old HTML with `index-BWXB7S1w.js`. A fresh request returned the correct deployed `index-55CB_99c.js`, matching the local build. Use a hard refresh or [the release URL](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=1c12046) when continuing an already-open tab. This is distinct from the server interpretation fix.

Remaining validation: explicit permission to upload the real `demo_movie_kanapp.mp4` to `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/api/runs/upload`, then repeat the fresh LIVE flow. Deployment and synthetic LIVE verification are complete; they are not represented as post-deploy LIVE verification of the owner's footage.
