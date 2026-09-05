# Studio repeat review and gstack QA

Subsequent LIVE deployment and QA are recorded in [Studio deployment](deployment-2026-09-05-studio.md) and [LIVE QA](qa-live-2026-09-05-studio.md). The local-only results and authorization boundary below describe this earlier pass, not the current deployment state.

Date: 2026-09-05 KST. Scope: Studio delta after `270d37d`, with this repeat pass starting at `ca87a05`.
Tested source: `91ef980` (includes `40aff61`, `126080f`). Local URL: `http://127.0.0.1:18131/studio`.

## Result and boundaries

- gstack review and browser QA found 13 concrete issues; all received narrow fixes. No unresolved issue from this scoped pass remains. Busy-step navigation was hardened as well.
- Frontend: **29 tests in 10 files PASS**, ESLint PASS, TypeScript/Vite production build PASS, `git diff --check` PASS. Five new regression tests cover workflow selection, existing-result navigation, external-file identity, custom volume values and invalid times.
- Backend source was not changed in this pass. The previous 349-test result is historical, not a new full backend test result. Real local API/media workflows were exercised below.
- The classic `/` page and desktop three-column / six-step Studio layout are preserved.
- This is **FIXTURE QA**, not LIVE Gemini/ClickHouse verification. Speech transcription, LIVE smart scene search, public memory policy and Cloud Run readiness were not re-certified.
- Both successful browser runs stopped before final delivery approval. No Approved Edit Memory writes, cloud data writes or production deployment were performed.
- The installed Windows gstack browser is `C:\Users\KAN\.codex\skills\gstack\browse\dist\browse.exe`. An extensionless `browse` check incorrectly misses it. This pass used the actual executable, not a substitute browser.

## Findings and fixes

| ID | Severity / area | Reproduction and observed problem | Fix and verification |
| --- | --- | --- | --- |
| 01 | High / functional | External verification clears `generated_version_url`; the old approval handler returned without contacting the approval API. | Bind the local uploaded file to the returned run ID and proof version label. Separate approval from availability of a generated download URL. External PASS now has a playable video and an enabled approval CTA. Final click was deliberately not executed. |
| 02 | Medium / functional | After a failed external verification, the external-upload control disappeared. | Added Upload corrected edit to BLOCKED recovery. Same run accepted corrected bytes and reached READY. |
| 03 | Medium / functional | Back to Plan offered Create previews again although the backend only accepts that transition before previews exist. Revisiting Edits could create another run. | Existing-plan actions now navigate to saved Plan/Compare results. Browser traversed Compare → Plan → Edits → Plan → Compare without a new request. |
| 04 | Medium / functional | Select only item 2, generate previews, return to Plan: server subset is reindexed but selected indices remained `[1]`; the sole applied edit appeared skipped. | Frozen preview plans use all server-returned operations. The sole edit is checked and Continue to previews stays enabled. Unit regression added. |
| 05 | Medium / content | Uncheck both items: 0 checked inputs but footer reported 2 edits selected. | Count the actual reviewed plan. Now shows 0, disables generation and explains that at least one edit is required. Before/after screenshots retained. |
| 06 | Medium / UX | Approved edits → New review cleared the run but left the library visible. | New review returns to the workflow. Browser verified Choose your edits and no library panel. |
| 07 | Medium / accessibility | At 390px, Approved edits and Classic UI were `display:none`. | Preserve 44px icon buttons with accessible names and titles; all three navigation actions are present and usable. |
| 08 | Medium / UX | Empty overlay text disabled Check plan without showing its reason; negative/missing times showed an unhelpful range summary. | Render plan validation beside settings and a specific invalid-time message. Verified empty text and negative time in browser; missing/negative time covered by unit test. |
| 09 | Medium / functional | Volume slider accepts -5 dB but the preset selector had no matching option. | Add a custom option for non-preset values. Keyboard -6 → -5 updates both controls to -5. Unit regression added. |
| 10 | Medium / functional | Company logo template bypassed the tool-list 24-edit cap. | Guard both template button and upload handler. At 24 edits, Duplicate and Company logo are disabled. A normal 3-edit logo upload still succeeds. |
| 11 | High / visual | At 390×844, action bar height was fixed at 72px; primary button bottom was 875.39px, below the viewport. | Let the wrapped action bar determine its height. Final button bottom is 837px at height 844. Additional 320, 768, 940 and 1280px checks pass. |
| 12 | Low / visual | Shared classic `footer` styles overrode Studio copy with Consolas. | Scoped Studio footer font inheritance. Browser computed style is now Manrope Variable; classic stylesheet is untouched. |
| 13 | Low / content | Upload area promised drag-and-drop but the existing input supports file browsing, with no drop handler. | Corrected the label to Choose a video to upload; no new upload mechanism implied. Source review and final browser copy check. |

Source commits: workflow/copy/menu semantics `40aff61`; editor inputs `126080f`; responsive/footer styling `91ef980`.

## Browser execution evidence

The local server was initially stopped. Started an isolated FIXTURE runtime at `runtime/qa-20260905` with intelligence enabled and copied existing demo media into it. This does not seed LIVE memory or call cloud AI.

1. Sample → Promo highlight → Check plan. Unchecked both items, verified 0 selection and disabled preview action. Selected only the second item, generated previews, returned through earlier steps, confirmed the selected subset remained intact.
2. Run `01M1R6CVY5M26ZFQ8FZCAF64TD`: selected A for the text-only subset. Uploaded unchanged `revisionproof_v1.mp4` as an external edit: BLOCKED, 2/3 checks pass. Reuploaded that run's selected `previews/A.mp4`: READY. Approval screen video `readyState=4`, blob URL belongs to this run/version, CTA enabled. Server `delivery_approved=false`, `generated_version_url=null` as expected for an external file.
3. Approved edits → New review returned to Edits. Empty text validation appeared. Negative start time displayed a correction message. Slider keyboard input showed custom -5 dB consistently.
4. Added 24 edits through the UI. Duplicate and Company logo disabled at the limit. Started a new review and replaced the source with the local sample MP4 via actual file upload.
5. Run `01M1R6SAVN9P50FSRVB482GZGW`: original upload + 1.5x speed on 0–8s + -6 dB volume on 0–8s + full-video logo. Created A/B previews, chose B, built full video. READY / **3 PASS** (`approved_patch`, `locked_cta`, `locked_audio`), `delivery_approved=false`. Generated video returned HTTP 206 for playback.
6. During source processing, all six workflow navigation buttons and New review were disabled. Original source/edits remained intact.
7. Checked viewport widths 320, 390, 768, 940, 1280. Document scroll width equaled viewport width; primary action stayed inside viewport. Desktop layout retained three columns.
8. Clicked Classic UI: `/`, no `.rp-studio`, heading Turn client notes into a verified video. No console errors.
9. Final workflow network: logo 201, source upload 201, previews 200, candidate selection 200, automatic version 200, generated media 206. No failed requests in the observed final workflow. gstack local navigation timing: DOM ready/load 33ms; this is a local warm-page measurement, not production performance.

### Visual evidence

Images are local QA artifacts under ignored `runtime/qa-screenshots/`, not production evidence. Each captured image was opened and visually inspected. Some source-review findings have DOM/API evidence rather than a pre-fix screenshot; no missing screenshot is represented as captured.

- `reqa-zero-before.png`, `reqa-zero-after.png`: zero-selection mismatch and correction.
- `reqa-external-blocked.png`, `reqa-external-pass.png`: external correction path and approval-ready player.
- `reqa-mobile-input.png`, `reqa-mobile-final.png`: initial clipped mobile footer and final fully visible controls.
- `reqa-compound-pass.png`: uploaded-source speed/volume/logo full-video PASS.

Rubric score for these exercised paths only: **83.05 → 100**. Baseline categories: console 100, links 100, visual 82, functional 45, UX 84, performance 100, content 89, accessibility 92. Final categories have no remaining deduction from the 13 findings. This issue-based score does not mean exhaustive accessibility, security, LIVE integration or final approval coverage.

## Backup and release boundary

- Pre-Studio backup: `backup/pre-studio-ui-20260904` → `270d37db02c8b05f99068778066140cc9e34eadd`.
- Pre-repeat-QA backup: `backup/pre-studio-reqa-20260905` → `ca87a05`.
- To inspect or restore source without destroying the current branch, create a separate worktree/branch from either backup. Do not reset the active checkout or force-push. Rebuild the frontend and follow the existing deployment runbook for a production rollback.
- Google reauthentication was unresolved before this pass. No new Cloud Run deployment was attempted in this repeat-QA pass. The previous deployed revision record is `revisionproof-staging-00025-88t`, source `0811382`, and was not re-queried here. This document does not claim Studio is deployed.
- Local run state and external-file blob URLs are session-local. Refresh starts a new UI session; existing architecture does not provide run restoration.
