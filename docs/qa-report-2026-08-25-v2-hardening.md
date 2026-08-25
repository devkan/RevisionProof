# QA evidence — v2 hardening, 2026-08-25

## Result

Status: **PASS for the fixture hackathon path after one verified mobile fix.** gstack health score moved from **99/100 to 100/100** after the default three-note input was made fully visible at 375 px.

This report supersedes the earlier fixture-slice report for the `review/qa-hardening` branch. It does not claim that credential-dependent Google Cloud or ClickHouse Cloud integrations have run.

## Browser path exercised

gstack browse tested the FastAPI-served React SPA at `http://127.0.0.1:8000`:

1. Runtime loaded as visibly labeled `FIXTURE`, with an explicit “not live evidence” banner.
2. The prefilled brief produced exactly three cards: `AUTO PREVIEW`, `CLARIFY`, and `MANUAL`.
3. Only the safe note produced three fixture evidence anchors and 1.05x/1.12x six-second previews.
4. Human approval of B froze a SHA-256 `RevisionSpec` containing its verification manifest.
5. v2 produced patch PASS, CTA FAIL, audio PASS, before/after CTA frames, `PUBLISH BLOCKED`, and a disabled Delivery button.
6. v3 produced three PASS checks, `PUBLISH READY`, and an enabled Delivery button.
7. Human delivery approval added event 12 and changed the button to `Approved for Delivery`.
8. Raw run JSON reported `READY`, three notes, 12 events, and `delivery_approved: true`.
9. The uploaded `/versions/v3.mp4` public-media path returned 404 as designed.
10. `OFFLINE_REHEARSAL` displayed a read-only banner, disabled the start button, and rejected a direct mutation with HTTP 409.

Console errors caused by the app: **0**. Broken application requests: **0**. The deliberate private-media probe returned its expected 404 and was excluded from error scoring.

## Responsive finding and fix

`ISSUE-001` (Medium, UX): at 375x812 the three-line demo brief wrapped beyond the 112 px textarea, hiding the third note on first view.

- Fix: mobile minimum textarea height changed to 186 px.
- Verification: `clientHeight=184`, `scrollHeight=184`, all three notes visible without inner scrolling.
- Horizontal overflow: `scrollWidth=375`, `clientWidth=375`.
- Interactive targets below 44 px: 0.
- Regression commit: `3c422bc fix(qa): ISSUE-001 — show all demo notes on mobile`.

## Performance observations

- Initial local document response: 66 ms in the recorded desktop run.
- A/B preview request: 1.462 s.
- v2 verification request: 2.084 s.
- v3 verification request: 1.782 s.
- Preview and proof images returned HTTP 200/206; no failed user-flow requests were observed.

These are local observations, not Cloud Run cold-start measurements.

## Automated evidence

- 35 backend tests pass.
- Ruff check and format check pass.
- ESLint and the Vite production build pass.
- The 30-note safety corpus is exactly 12 auto-previewable, 9 clarification, and 9 manual-creative cases.
- The 12-video regression corpus retains 9 expected failures with zero false PASS results.
- Three consecutive real-media rehearsals finish with v2 BLOCKED, v3 READY, delivery approved, and 12 events.
- Docker rebuild was attempted but not run because the local Docker Desktop Linux daemon was stopped. The current non-root image change therefore remains a container-runtime verification item.

## Review findings not presented as complete

- Google ADK/Gemini, Vertex embedding, GCS, ClickHouse Cloud TLS, the official MCP path against the target cloud database, and Cloud Run deployment remain credential-unverified.
- The in-memory run snapshot cannot hydrate after a Cloud Run restart. `max-instances=1` avoids cross-instance splits but is not durable recovery.
- No push, pull request, cloud deployment, or billable resource creation was performed.

Screenshot artifacts are kept in the ignored local QA output under `.gstack/qa-reports/screenshots/` and `runtime/qa-screenshots/`.
