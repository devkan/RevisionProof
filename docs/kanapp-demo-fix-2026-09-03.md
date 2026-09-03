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

## Release boundary

The fixes have passed local tests. The preceding LIVE revision is `revisionproof-staging-00016-j4q`; this record will receive the new build/revision and fresh LIVE verification after deployment. Preserve the current project, pinned ClickHouse secrets, read-only memory, 4 GiB / 2 CPU / concurrency 4 / min-max 1, and final delivery approval boundary.
