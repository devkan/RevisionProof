# Studio hands-on LIVE QA

Date: 2026-09-05 KST. Status: **review, QA fixes, deployment and final canary complete**.

## Follow-up: Check plan disabled without an explanation (local fix, not deployed)

Reported after the deployment below, using screenshot `618.png`. The earlier completion statement describes the earlier release only. This follow-up is verified locally on `http://127.0.0.1:18131/studio` in FIXTURE mode; it has not been committed, pushed or deployed to Cloud Run.

### DEBUG REPORT

- **Symptom:** Plan's Check plan action was disabled, both cut and zoom appeared READY, and the blocking reason was absent from the Plan screen/footer.
- **Root cause:** Edit 3 cuts original time 0–4s, while Edit 4 zooms that same 0–4s. `planProblem` correctly rejects an edit entirely removed by a cut. Studio only displayed that string in the Edits sidebar and independently marked included rows READY. Disabled pre-check checkboxes and misleading selection instructions added confusion.
- **Fix:** `frontend/src/editing.ts:44` returns structured issues with original edit indexes and actionable messages. The existing `planProblem` contract still returns the first blocking string. Validation rules and server checks remain enforced. `frontend/src/StudioApp.tsx:177` renders the issue list; Plan, revision badges, and footer use the same issues. `Fix edit N` opens that exact draft editor and moves keyboard focus. Pre-check rows have numbered Edit/Watch actions; selection checkboxes remain available after Check plan. Footer reasons wrap instead of being clipped, and the disabled action references them with `aria-describedby`. Six-step/three-column layout and classic route remain intact.
- **Regression test:** `frontend/src/studioPlanValidation.regression.test.tsx`, 12 cases. Failed before implementation, passed after. Covers the five-edit screenshot, adjacent cuts, partially retained footage, invalid fields, speed/volume/zoom/overlay conflicts, original row numbering in selected subsets, accessible issue markup and empty selections.
- **Evidence:** `npm test`: **13 files / 63 passed**; ESLint and TypeScript/Vite build passed. Backend: **349 passed, 1 warning in 127.13s**. Warning is an existing Windows `.pytest_cache` write permission warning, not a test failure. Final local bundle: `index-BZbfM4yW.js`, `index-B4WNcQg1.css`.
- **Browser QA:** Reproduced the old failure with sample cut 0–4s + zoom 0–4s. Recreated five edits using two subtitles, cut, zoom and a synthetic logo. Plan and footer identify Edit 4 and Edit 3; both rows show NEEDS FIX. At 1440×900 and 390×844 there was no document-width overflow and the footer reason/action was visible. On mobile, Fix edit 4 opened revision 04's Zoom settings. Changing zoom to 4–8s cleared the warning and enabled Check plan. Five edits were preserved. Unchecking every reviewed edit produced a visible minimum-selection message; Review issues focused the notice, and selecting again restored the action. Empty text + reversed times showed both errors; fixing both enabled the action. An unconverted request showed its blocker, which cleared when the request was cleared.
- **End-to-end:** Local run `01M1RH7XB36WMMWRDMA7P2CN7K` created A/B previews, selected A, rendered the full 26s video from a 30s sample, and reached **READY / PASS / 3 checks PASS**. `delivery_approved=false`. No user draft was changed, no actual KANAPP video was uploaded, and no final delivery or memory write was performed. Browser console errors: none observed.
- **Related:** This is a missed invalid-combination UX case, separate from the previous preparation-range and preview-count defects. The previous QA score was not exhaustive evidence for every input combination.
- **Status:** DONE_WITH_CONCERNS: local fix and QA complete; push and cloud deployment are not part of this follow-up's completed results. Existing open tabs still hold the previous JavaScript. Do not reload the user's current draft; to continue immediately, use Back to Edits and move Zoom 04 to retained source footage (for example 4–8s), or remove the conflicting edit.

Local ignored screenshots under `runtime/qa-screenshots/`:

- `plan-block-before-20260905.png`
- `plan-block-after-20260905.png`
- `plan-block-mobile-20260905.png`
- `plan-fixed-full-check-20260905.png` (before the final CSS-only adjustment that keeps read-only revision labels at full opacity)

## Scope and method

gstack `/review`, `/qa` and `/browse` were used with source inspection, real browser interaction, rendered screenshots, request outcomes, persisted run snapshots and regression tests. `/investigate` traced the upload failure before changing code. The installed QA package lacks its referenced report template and issue taxonomy files, so the repository's existing report structure is used with the skill's scoring rubric.

The layout and classic page are preserved. Only synthetic QA media and the existing public sample were used. This is not a claim that every possible input, browser or concurrency pattern is tested. Final delivery approval/download and Approved Edit Memory writes are deliberately not exercised.

## Issues and fixes

| ID | Severity / category | Finding | Fix | Verification |
| --- | --- | --- | --- | --- |
| ISSUE-LIVE-001 | High / functional | Whole-video silence removal fails upload's legacy 4–8s preparation gate; short captions/cuts share the cause | `ab5a6b8` — independent preparation anchor, full plan retained | Verified: twice reproduced LIVE; 16 new regression cases; post-deploy upload, suggestions, preview and full checks passed; 2s caption plan also accepted |
| ISSUE-LIVE-002 | Medium / UX and content | Cut-only A preview is described as two versions; singular counts are plural | `3ca72e4` — count-aware instructions and labels; `44cc8c0` — final Applied count | Verified instructions: before/after screenshots, 6 new tests, LIVE A selection and full checks. Last one-line Applied label verified in a fresh local full workflow; final bundle and service canary verified |

Files changed: `frontend/src/StudioApp.tsx`, `frontend/src/studioWorkflow.ts`, new `studioUploadRange.regression-1.test.ts` and `studioPreviewCopy.regression-1.test.ts`. No existing tests, classic UI, backend, CSS, CI, database schema, secrets or infrastructure settings were changed.

Before/after evidence (local ignored artifacts):

- ISSUE-LIVE-001 before: `runtime/qa-screenshots/studio-live-silence-error-20260905.png`; local after: `studio-local-silence-fixed-20260905.png`.
- ISSUE-LIVE-002 before: `runtime/qa-screenshots/studio-local-single-preview-before-20260905.png`; local after: `studio-local-single-preview-fixed-20260905.png`.
- LIVE fixes: `studio-live-silence-fixed-20260905.png`, `studio-live-single-preview-fixed-20260905.png`, `studio-live-silence-ready-20260905.png`. Last Applied count local after: `studio-local-approval-count-fixed-20260905.png`.
- Initial LIVE compound preview, PASS and mobile: `studio-live-compound-previews-20260905.png`, `studio-live-compound-ready-20260905.png`, `studio-live-compound-mobile-20260905.png`.
- External negative and recovery: `studio-live-external-rejected-20260905.png`, `studio-live-external-blocked-20260905.png`, `studio-live-external-corrected-20260905.png`.

## Exercised workflows

See [deployment identity and run evidence](deployment-2026-09-05-studio.md) for exact build, revision, source, hashes and run IDs.

- Uploaded source, logo validation/upload, mixed Korean/English speech transcription and editable correction.
- Speed, volume, logo and three captions → choose B → full render → READY / 3 PASS → synchronized original/result playback → approval screen without approving delivery.
- Smart finder off-state, opt-in search/index, chosen scene timing, editable natural-language draft, zoom, text, manual subtitle and cut → A/B → frozen Plan round-trip → choose A.
- External wrong-duration rejection (409), duration-matched but incomplete edit BLOCKED, corrected exact candidate READY / 3 PASS. Corrected external video uses a loaded blob URL (readyState 4), not an unrelated server-generated version. Delivery approval remains false.
- Empty read-only approved-edit library is valid; no save button is available.
- Post-fix LIVE run `01M1REEYNYAKDJ2EF1KPCRRE4F`: source upload → four unchecked quiet-cut suggestions → select 1.1–1.8s only → single A preview → READY / 3 PASS. Output 9.233333s, exact approved-file match, Change Map `mcp-clickhouse.run_query`, zero residual deltas, delivery false.
- Focused LIVE run `01M1REMECEG9K0XRQGYDJ3ZC6H`: a 0–2s caption-only plan was accepted without changing its timing. No full render is claimed for this focused probe.
- Fresh final-source local run `01M1RF5761Z6Q9D1XQPXDC7171`: 0–0.5s cut → A → full PASS → approval summary reads `Applied 1 edit`, delivery not approved.
- 320/390/768px LIVE document widths matched each viewport, CTA remained within the viewport; 1280px three-column layout retained. Classic UI navigation clicked successfully. These full functional runs were on revision 00027; the last follow-up changes only one summary label.

## Test gates and console baseline

- Backend **349 passed**, current-turn full suite; backend unchanged by both fixes.
- Final frontend **51 passed / 12 files**; lint, TypeScript and production build passed. Separate Windows sandbox `spawn EPERM` was resolved by running the identical command with approved process permissions.
- Final expected asset: `index-BmgsfeTd.js`; CSS `index-BTRL_Fp0.css`. The 51-test, lint and build gates were repeated after the one-line copy follow-up.
- Pre-fix console showed two unexpected 422s at `08:56:33.232Z` and `08:58:24.928Z` (ISSUE-LIVE-001), and one intentional negative-test 409 at `08:57:24.867Z`. gstack aggregates console events across tabs despite labeling output with the current tab URL. The buffer was cleared only after preserving these details, for a fresh final canary.
- Cloud Build and local gates are distinct from GitHub Actions: the private working branch does not trigger main/PR-only hosted CI.

## Health score

Observed-path score only; not an accessibility certification or performance benchmark. Intentional negative-test rejection is excluded from defects.

| Category | Weight | Before | Final |
| --- | ---: | ---: | ---: |
| Console | 15% | 70 | 100 |
| Links | 10% | 100 | 100 |
| Visual | 10% | 100 | 100 |
| Functional | 20% | 85 | 100 |
| UX | 15% | 92 | 100 |
| Performance | 10% | 100 | 100 |
| Content | 5% | 92 | 100 |
| Accessibility | 15% | 100 | 100 |

Observed-path health score: **90.9 → 100 / 100**. Two issues found, both fixed and verified (2 verified, 0 best-effort, 0 reverted, 0 deferred newly discovered bugs). The Applied label follow-up is part of ISSUE-LIVE-002, not another functional defect. Final-source local rendering confirms that label; final LIVE canary confirms the deployed bundle and unchanged service contracts. This score means no unresolved observed issue in this scoped pass, not exhaustive defect freedom.

PR-ready summary (no PR was created): "QA found 2 issues, fixed 2, observed-path health score 90.9 → 100."

Final revision `revisionproof-staging-00028-n4z`, 100% traffic, Ready/ConfigurationsReady/RoutesReady True; build `660dbd2f-1bf5-4ab1-9cb1-59c41277b340` SUCCESS. Final LIVE bundle `index-BmgsfeTd.js`, all three status endpoints 200, no new console errors. Fresh canary plan `01M1RFPEN1BG17X6MZQ8B0ZF6V` accepted the selected sample cut. The local final-label check is not mislabeled as another full LIVE render.

## Remaining test boundaries

- Final 00028 canary also opened the optional approved-edit search to completion: `No saved edits yet`, saving disabled, no new console errors.
- Final delivery approval/download and memory saving require owner action, not automated approval.
- The actual KANAPP demo scenarios and private original remain separate from this synthetic-media QA.
- Process-local runs do not survive every restart. JSON evidence was saved before deploying over the initial test revision.
