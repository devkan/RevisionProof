# QA evidence — submission smoke, 2026-08-27

Result: **scoped read-only smoke PASS; submission gates remain open**. Method: gstack `qa-only`. No new end-to-end run, approval, deployment, or cloud configuration change was performed.

## Fresh observations

- The [LIVE app](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app) and its assets returned HTTP 200 with no observed failed requests or browser console errors.
- `/health`: `status=ok`, `mode=LIVE`. `/ready`: `status=ready`, `live_credentials_configured=true`. `/api/runtime`: `live_ready=true`, no missing settings. Readiness deliberately does not assert per-run integration success.
- GET of run `01M0Z3338TYVHWHK4FZRGADTKZ` returned `READY`, proof `PASS`, three passing checks, `delivery_approved=true`, and 14 events. Its Gemini/MCP source labels and spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5` are unchanged.
- The final event is the existing human approval at `2026-08-26T13:48:30.750541Z`, not a new approval today.
- Full-page screenshots at desktop 1280 × 800 and mobile 375 × 812 were inspected. Mobile document width was 375 with no horizontal overflow. The feedback field has an associated label; this is not a full accessibility audit.
- One warm page load measured 1,144 ms, with TTFB 277 ms. No cold-start, load, or percentile claim is made.
- Source MP4, candidate B MP4, and the two current CTA evidence PNGs returned HTTP 206 for a 16-byte range request. This proves route availability, not full decoding/playback.

## Local artifacts

The detailed report and screenshots are intentionally ignored by Git under `.gstack/qa-reports/`:

- `qa-report-submission-smoke-2026-08-27.md`
- `baseline-submission-smoke-2026-08-27.json`
- `screenshots/submission-smoke-desktop-2026-08-27.png`
- `screenshots/submission-smoke-mobile-2026-08-27.png`

No overall weighted QA score is assigned because this smoke deliberately excludes mutation paths and several test categories. The linked template/taxonomy files were absent from the installed skill; the embedded report structure was used.

## Submission-document review findings

After the read-only browser phase, gstack `document-generate` research checked the relevant UI, adapters, workflow, media generator, tests, repository metadata, and official rules:

1. GitHub repository is **PRIVATE** and its default branch is `main`; the implementation is on `review/qa-hardening`. Neither visibility nor default branch was changed.
2. GitHub reported license `Other`. The existing `LICENSE` contained an Apache 2.0 notice but not its full terms. The missing official body was added without choosing a new license or changing the original copyright. Default-branch recognition remains to be checked after an owner-approved landing.
3. The sample's scene descriptions are authored metadata over synthetic graphics and a tone. The new submission copy explicitly avoids claiming transcription or real presenter footage.
4. Delivery approval records a state/event inside the app; it does not upload to a publishing platform. The submission script preserves that distinction.
5. Full restart recovery and active-run UI restoration remain unimplemented. Existing GCS/ClickHouse evidence must not be described as full application recovery.

See the [submission release gates](submission-pack-2026-08-27.md#release-gates--not-yet-submission-ready) and [recording script](demo-recording-script-2026-08-27.md).

## Documentation validation

- All 32 local Markdown links/anchors across the new documents, index, and handoff resolve; code fences are balanced and no replacement characters were detected.
- The completed license body exactly matches the official Apache 2.0 text, followed by the unchanged project copyright.
- `git diff --check` passes. No application code or deployment settings changed, so automated code suites were not rerun for this documentation-only checkpoint.
- The installed `gstack-redact` could not load its missing `../lib/redact-engine` dependency. A local added-lines credential-pattern scan and manual diff review were used instead; no credential was found. This is a limited fallback, not the full gstack redaction engine or a repository-history audit.

## Not rerun today

No fresh Gemini interpretation, MCP query, render, version upload, verification, SSE reconnect, or final approval was performed against the LIVE service. No direct GCS/ClickHouse count or IAM inspection was performed. The complete credential-backed flow and automated full-suite results remain historical evidence in the [2026-08-26 final LIVE report](qa-report-2026-08-26-live-final.md).
