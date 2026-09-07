# Codex independent review of Antigravity fixes

- Date: 2026-09-07 KST
- Branch: `fix/qa-followup-bugs-20260907`
- Base and freshly fetched `origin/main`: `9fd3411943e8dacb5120849881523e7ff1bbccd7`
- Reviewed: three modified application files and two new regression test files, all uncommitted.
- Result: **The three functional fixes work in the independent local checks. Two pre-merge findings remain.**
- This review did not change application source, tests, configuration, or the existing Antigravity evidence. SHA-256 checks confirmed all five reviewed source/test files stayed identical during review. No commit, push, merge, deployment, or cloud API execution was performed.

## Findings

### 1. [P1] Backend CI lint currently fails (confidence: 10/10)

The repository's actual CI runs both `ruff check backend scripts` and `ruff format --check backend scripts`. Neither gate is satisfied by the current change:

- `backend/src/revisionproof/editing/render.py:48`: E501, 104 characters against the configured 100-character limit; the same condition also fails the format check.
- `backend/tests/test_text_wrap_regression.py:1`: I001 import ordering and F401 unused `pytest` import.
- `backend/tests/test_text_wrap_regression.py:11` and `:47`: E501 overlong string assignment lines.

Fresh results: **5 lint errors; 1 file requires formatting**. Passing pytest, frontend ESLint, and the frontend build does not satisfy this separate backend CI gate.

Required correction: remove the unused import, apply the existing import/format conventions to the two affected Python files, split the long string literals without changing their value, and rerun both CI commands. No lint-rule relaxation or CI changes are needed.

### 2. [P2] The Issue C regression test does not exercise the original bug (confidence: 10/10)

`frontend/src/changeMapTransitions.regression.test.tsx:101` renders a fresh BLOCKED component with `renderToStaticMarkup`; lines 117-119 then render a separate fresh PASS component. No window is clicked and no mounted component receives new props. The selected state therefore never contains a previous failure window.

The exact Issue C test was run against the original `RevisionIntelligence.tsx` from `9fd3411`, substituted in memory by a temporary Vite plugin. It **still passed**, despite the original stale-selection bug being present:

```text
Tests  1 passed | 3 skipped (4)
```

The other tests were deliberately excluded to isolate C. A separate baseline run of all four new frontend cases failed the external-video test as expected, confirming that the baseline component substitution was effective.

Required correction: use a mounted React/browser test, click a review window, update the same run to a new analysis, and assert that both the detail explanation and old metrics change. Demonstrate failure with the old implementation and success with the fix. Static markup tests may remain as presentation tests.

## Fresh validation

| Check | Result |
| --- | --- |
| Backend full suite | **353 passed**, 132.19 seconds |
| Frontend full suite | **76 passed**, 16 test files |
| Frontend ESLint | PASS |
| Frontend TypeScript and production build | PASS |
| Backend Ruff lint | **FAIL**, 5 errors |
| Backend Ruff formatting | **FAIL**, 1 file |
| Git whitespace check | PASS |
| Source/test hashes before and after review | Unchanged |

The backend suite used the installed virtual environment with fresh, explicit temporary/cache paths. An initial targeted test attempt hit a missing diagnostic temporary directory; that setup issue was superseded by the successful complete suite above.

## Independently observed functional behavior

These are **local checks**, not a new staging deployment or a full live-provider workflow. The browser harness imported the current real `ChangeMap`, `ComparisonDialog`, and `checkedVideoUrl`, supplied synthetic verification snapshots, and played existing local MP4 files. It deliberately omitted the parent remount key to also exercise the component's own state handling.

- **A:** Executed the actual renderer for both `text` and `subtitle`, in A and B. The reported sentence retained all words. A used two lines; B used three with `professionals.` intact. All lines stayed within 1080 pixels. Oversized tokens stayed within the width limit without losing characters. Mixed Korean/English text and explicit blank lines were preserved. The generated A/B images were visually inspected.
- **B:** A current external blob URL enabled the comparison button. The real comparison dialog opened and both local video players advanced together from the selected four-second position. A mismatched external version made `checkedVideoUrl` unavailable and disabled the comparison button. The existing URL-helper tests also cover mismatched run IDs and generated-video precedence.
- **C:** Clicked the failed window before replacing the same run's snapshot with PASS. The detail immediately changed to the current requested-edit explanation, with no stale failure text. Also confirmed current-window lookup with an unchanged analysis ID, and safe fallback when the selected window disappeared.

No new functional defect was observed in these bounded checks. This does not substitute for a deployed end-to-end verification after an eventual approved release.

## Evidence and reproduction artifacts

Ignored local diagnostic artifacts are in `runtime/antigravity-review-20260907/`:

- `source-hashes-before.json`: identities of the five reviewed application/test files.
- `caption-check.json` and `fixed-{text,subtitle}-{A,B}.png`: measured and visual renderer results.
- `check-caption.py`: independent renderer/width/content checks.
- `RevisionIntelligence.baseline.txt`: original component from `9fd3411`.
- `vitest-baseline.config.mjs` and `baseline-c-test.log`: source-preserving baseline test comparison.
- `serve-review.mjs`: local component/player diagnostic harness; stopped after verification.

The existing [Antigravity fix report](fix-report-2026-09-07.md) and [original QA report](qa-review-2026-09-07.md) were preserved. Their existing B/C screenshots and recording show the pre-fix staging defects; they are not post-fix browser evidence.

## Next step

Return the two findings above to Antigravity, retain the three functional fixes, and re-review the small follow-up diff before integration. Merging and deployment remain separate from this review.
