# QA evidence - final LIVE deployment, 2026-08-26

## Result

Status: **PASS for the credential-backed LIVE hackathon flow. Final delivery approval intentionally not executed.**

Tracked commit `d1b9a10` was built by Cloud Build `d5845e1e-9123-4e81-81cb-0fb3f6b607ec` and deployed as Cloud Run revision `revisionproof-staging-00009-mbh` with 100% traffic. The pushed RevisionProof image digest is `sha256:54e2427d56e8408dfd712c4864df8dec555d127f4b1380a070bbfe2b662e73e3`.

## Runtime contract

- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- `/health`: `status=ok`, `version=0.1.0`, `mode=LIVE`
- `/ready`: `status=ready`, `live_credentials_configured=true`, `integration_execution_verified=false`
- `/api/runtime`: `mode=LIVE`, `mutable=true`, `live_ready=true`, no missing settings
- Cloud Run: concurrency 4, min 1, max 1, exact RevisionProof runtime service account

The readiness flag does not claim a process-wide integration call. The final run below supplies the call-level proof.

## gstack LIVE path

gstack exercised run `01M0Z3338TYVHWHK4FZRGADTKZ` through the public service:

1. The default three-note brief was submitted as a single line with inline `1.`, `2.`, and `3.` markers. It produced one `AUTO_PREVIEW`, one `CLARIFY`, and one `MANUAL` note.
2. Interpretation source was `google.vertex.gemini`. Three time-coded evidence anchors came from `mcp-clickhouse.run_query`.
3. With the resumable SSE connection still open, the preview mutation returned HTTP 200 in 2.973 seconds; no Cloud Run 429 occurred.
4. Candidate B froze the 1.12x patch and spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5`.
5. Uploaded `revisionproof_v2_blocked.mp4` passed the patch/audio checks, failed the locked CTA check, and entered `BLOCKED`.
6. Uploaded `revisionproof_v3_ready.mp4` passed all three checks and entered `READY`.
7. Raw JSON reported `delivery_approved=false`. The consequential `Approve for Delivery` action was not invoked.

Browser console errors: **0**. All mutation requests returned HTTP 200. At 375x812, `scrollWidth=375` and no horizontal overflow was present.

Observed timings:

- Navigation total: 506 ms; TTFB: 201 ms
- Preview render: 2.973 s
- Candidate approval: 1.521 s
- v2 upload/verification: 13.394 s
- v3 upload/verification: 11.237 s

Screenshots:

- `.gstack/qa-reports/screenshots/live-inline-evidence-fixed.png`
- `.gstack/qa-reports/screenshots/live-previews-no-429.png`
- `.gstack/qa-reports/screenshots/live-v2-blocked.png`
- `.gstack/qa-reports/screenshots/live-v3-ready-unapproved.png`
- `.gstack/qa-reports/screenshots/live-mobile-ready-375x812.png`

## Persistence and privilege evidence

- ClickHouse final-run counts: one spec, 24 feature rows, six check rows.
- ClickHouse safety counts: bootstrap admin 0, durable definer user 1, durable view replicas 4, preserved backup 1.
- Private GCS objects: v2 394,028 bytes; v3 394,983 bytes under the final run path.
- The preserved ClickHouse backup is `revisionproof.segments_pre_seed_dedupe_20260826` and was not modified or deleted.

## Defects found and fixed during LIVE QA

### ISSUE-001 - SSE starved mutations at Cloud Run concurrency 1

The long-lived `/events` request occupied the only instance slot, so the platform returned HTTP 429 for preview rendering. Cloud Run remains max 1 for process-local ownership but now uses concurrency 4. A static regression test locks this deployment contract. Final LIVE preview rendering returned HTTP 200 while SSE remained open.

### ISSUE-002 - inline numbered feedback failed grounding closed

The UI/browser could submit the three default notes as one line, while the server split only line-leading markers. Gemini returned three notes against one source note and the run correctly failed closed. The parser now recognizes sequential inline numbered markers; a regression test uses the exact newline-collapsed brief. Final LIVE interpretation produced all three notes and advanced normally.

## Automated gates

- Backend: 103 tests pass.
- Frontend: 4 tests across three files pass.
- Ruff check and format check pass.
- Frontend production build passes.
- `git diff --check` passes.

## Known boundary

Run snapshots, events, idempotency records, and local preview artifacts remain process-local. `max-instances=1` avoids simultaneous split ownership but a Cloud Run restart still requires starting a new run. ClickHouse audit rows and GCS candidates are durable evidence; they are not full runtime hydration.
