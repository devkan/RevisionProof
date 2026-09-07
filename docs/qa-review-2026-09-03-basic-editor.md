# Basic editor gstack review and QA — 2026-09-03

Status: review and fixes complete; subsequently deployed after explicit owner approval, with fresh LIVE checks passing. See [deployment evidence](deployment-2026-09-03-qa-fixes.md). Review scope: `2591cd8..918e314`; prior application source `1b2c0ae`, verified fixed source `94c081c`. GitHub default branch is `main`; this review focuses on the newly shipped basic editor rather than repeating the entire earlier branch audit. No open PR. Working tree was clean at start.

Targets: existing LIVE Cloud Run service and isolated local FIXTURE server on port 18129. Real KANAPP media remains local; LIVE tests use synthetic media. Final delivery approval is never submitted.

Applied gstack `review` (mandatory checklist, critical and informational passes, API specialist) and `qa` (Standard, diff aware, desktop/mobile and error states). The installed QA package lacks its referenced template/taxonomy files; the report uses the workflow's inline categories and scoring rubric.

## Findings

### ISSUE-001 — Stale draft survives a source-video change

Medium / P2, confidence 10/10. `frontend/src/EditComposer.tsx` retains a draft based only on the request text, while `App.tsx` reuses the component across sources. Reproduced twice in LIVE: choose the synthetic 10s clip, request a caption with no times, obtain a 0–10s draft; switch to the 30s sample and enter the same request. The old 0–10s draft reappears without interpretation even though the UI promises whole-video timing.

Evidence: `.gstack/qa-reports/review-2026-09-03/screenshots/draft-source-before.png`, `issue-001-result.png`.

Fixed in `0d42684`: key the request component by source URL so it resets on a video change. Browser re-test: no old draft appears after switching, then fresh interpretation uses 0–30s. Evidence: `issue-001-after.png`.

### ISSUE-002 — Correct cut export can falsely become BLOCKED

High / P1, confidence 10/10. `backend/src/revisionproof/editing/verify.py` independently seeks fractional times in the output and original. Floating point rounding around half-frame timestamps can compare adjacent frames after a cut. A 4s alternating-frame synthetic with a 0.1–0.2s cut produces an exactly correct 117-frame export, yet the mapped scene check fails 5/7 samples. Export hash identity passes. Fix must address frame correspondence, preserving the visual threshold and tamper checks.

Fixed in `82d51a3`, regression test in `94c081c`: quantize the output frame once, map it to the source frame, then use explicit frame indices for verification and Change Map. Visual-edit classification uses that same frame; legacy timing remains unchanged. Regression before: 1 failed / 1 passed; after: 2 passed. Browser re-test run `01M1KM2RS7402YXTT68AVMSTZW`: READY, all three checks PASS, delivery approval false. Evidence: `issue-002-before.png`, `issue-002-after.png` and `.gstack/qa-frame-mapping-{before,after}/test_approved_frames_do_not_fa0/frame-mapping-proof.json`.

### ISSUE-003 — Local caption-removal request suggests deleting footage

Medium / P2, confidence 10/10. Local rules parse `2–4초 자막 삭제` / `Remove the text from 2–4s` as a time cut, although removal of burned-in text is unsupported. LIVE instructions already prohibit that interpretation. Local drafts must return no destructive operation and explain the supported alternative.

Fixed in `6cbd34e`, six regression cases in `7e392d8`. Both languages reproduced before the fix. Browser re-test returns no operation, disables use of the draft and explains the limitation. Explicit footage cuts and quoted text containing removal words still work. Evidence: `issue-003-before.png`, `issue-003-after.png`.

### ISSUE-004 — Generic warning on ordinary LIVE text insertion

Low / P3, confidence 9/10. LIVE Gemini sometimes adds the burned-in-text limitation even for a simple request to add new text. The draft and execution remain correct. Deferred under Standard QA; this is wording noise, not the old text-insertion refusal. Current UI already explains the limitation beside edit controls. No other unresolved medium/high findings in this review scope.

## Baseline checks

- LIVE page and runtime load; initial current-session console errors: zero. Earlier 409 errors from prior releases were excluded by timestamp and the log buffer cleared after recording them.
- 25 MiB video selection shows the 24 MiB limit warning before any upload request.
- LIVE Korean literal-caption draft succeeds; English words preserved exactly. It also includes an unnecessary generic burned-in-text warning (low UX issue; not an execution blocker).

## Verification results

- Full backend: **330 passed in 124.10s**, including legacy specs, uploads, failed/tampered exports, new caption-removal and frame-mapping regressions. Frontend: **22 passed / 8 files**. Ruff check/format (63 files), ESLint, TypeScript and production build pass. No existing tests were modified for these QA fixes.
- Current local compound run `01M1KKXEXAJM93CJCJ94GA598V`: Korean top subtitle 0–3s, zoom and English bottom text 4–10s, explicit cut 0.5–1s, selected quiet cut 3.133333–4.866667s. A/B generated; B reached READY / 3 PASS, 10s became 7.766667s, map had zero review flags. Quiet cuts start unchecked and require selection.
- Actual downloaded MP4 and selected B preview both SHA-256 `8314789675af1872962ca99d6911df4c6b6c0aebefc020b8fba09691e36b49aa`. Korean caption visible in `compound-ready.png`, English lower caption and zoom visible in decoded `export-text.png`. Evidence JSON: `.gstack/qa-reports/review-2026-09-03/compound-run.json`.
- Compare seek: revised 3s maps to original 5.233333s. Escape closes the native comparison dialog and restores focus to its trigger. Adjust edits preserves original file, all five requested operations and full Korean request text.
- Invalid start −1 blocks Review edit plan and identifies Edit 1. Restoring 0 permits continuing. 25 MiB and 61s files show actionable warnings; original selection stays usable.
- Desktop 1440px and mobile 390px reviewed. Five edit cards and their fields remain usable; `document.body.scrollWidth === innerWidth === 390`. Screenshots: `initial.png`, `mobile-baseline.png`, `mobile-edit-controls.png`. Full-page captures can place the sticky header at the captured scroll offset; no page overflow was found.
- New QA console: zero errors; recorded QA resource requests: none with status >=400. Earlier release 409 logs were excluded. The old BLOCKED result itself returned HTTP 200, as expected for a completed verification.
- Final human delivery approval was not clicked. No real KANAPP video was sent to LIVE, no Cloud memory saved, no infrastructure or credentials changed.

## Standard QA score

| Category | Weight | Before | After |
| --- | ---: | ---: | ---: |
| Console | 15% | 100 | 100 |
| Links | 10% | 100 | 100 |
| Visual | 10% | 100 | 100 |
| Functional | 20% | 69 | 100 |
| UX | 15% | 97 | 97 |
| Performance | 10% | 100 | 100 |
| Content | 5% | 100 | 100 |
| Accessibility | 15% | 100 | 100 |

Weighted score: **93.35 → 99.55**. Before: 1 high, 2 medium, 1 low; after: 1 deferred low. Scores reflect observed issues in the basic-editor flow, not a full accessibility certification or load benchmark. The top three fixes are ISSUE-002 (false block), ISSUE-001 (stale source draft), and ISSUE-003 (destructive interpretation).

## Historical release boundary and prepared artifact

At the end of QA, Cloud Console read access was rejected by automatic approval review because it considered the private destination outside the local QA scope. This was **not** a manual user rejection. No workaround or alternate browser was used. The owner then explicitly requested deployment; the same Cloud Shell path succeeded and source `94c081c` is now live on revision `revisionproof-staging-00022-swm`. This section preserves the earlier boundary and archive provenance.

Prepared during QA, subsequently uploaded and verified during the approved deployment:
- Source commit `94c081c`, archive `.gstack/revisionproof-deploy-94c081c.zip`, SHA-256 `226c367ce8309e42b63ff148c51277681860d3c51e5890a61ba7d081a5a39f69`.
- Bundle `.gstack/revisionproof-release-94c081c-bundle.zip`, SHA-256 `03ba82e98e419f9608518309c42de79483183d6a30ff190f0d83c913f5a58190`.
- Helper `.gstack/rp-release-94c081c.sh`, cloned from the verified previous helper with only commit/archive paths and expected hash changed. It retains project/account/resource/secret checks. No media or secrets included.

The approved deployment used this bundle, passed the existing-service preflight, and repeated the odd-frame cut and compound synthetic LIVE checks successfully. Existing resources and final human delivery gate were preserved.
