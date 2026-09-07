# Antigravity QA fixes: integration and release

Date: 2026-09-07 KST. Status: **Prepared for authorized commit, merge and deployment; final execution evidence will be appended after verification.**

## Scope and attribution

The owner authorized committing, merging, and deploying the three fixes implemented using Google Antigravity. Codex independently reviewed the changes, requested two bounded follow-ups, and confirmed both were resolved. Existing development history is preserved; this release does not reattribute earlier implementation.

- English captions wrap at word boundaries, with character fallback for oversized tokens.
- Studio passes the current verified external-video URL to Change Map for comparison.
- Change Map derives selected details from the current analysis instead of retaining the previous failed window object.
- Regression coverage adds four caption tests and six B/C tests, including three mounted React state transitions. `happy-dom` is a development-only dependency.
- Source branch: `fix/qa-followup-bugs-20260907`; initial base: `9fd3411943e8dacb5120849881523e7ff1bbccd7`.

See the [final independent re-review](review-2026-09-07-antigravity-supplement.md), [first review](review-2026-09-07-antigravity-fixes.md), [Antigravity supplement](fix-supplement-2026-09-07.md), [fix report](fix-report-2026-09-07.md), and [original staging reproduction](qa-review-2026-09-07.md).

## Verified preparation

- Reviewed source/test/package hashes match the accepted re-review.
- Backend full suite was independently verified at 353 passed in the first review; the formatting-only follow-up passed the four caption cases again.
- Latest re-review: frontend 78 tests/16 files, lint and build passed; backend Ruff lint and format passed for all 81 Python files.
- The same B/C tests on original `9fd3411` failed four behavioral assertions; current source passed all six.
- Runtime dependencies and deterministic approval/verification contracts are unchanged.
- Commit the named reproduction recording and referenced screenshots. Browser-generated `page@*.webm` raw recordings remain preserved locally and are ignored; they include duplicate/intermediate captures and are not additional verification claims.

## Deployment target and recovery

- Existing project: `revisionproof-agentic-2026-kan`, number `348672234012`, label `managed-by=revisionproof-gcp`.
- Account: `secureis@gmail.com`; region: `us-central1`; service: `revisionproof-staging`.
- Known previous deployment: source `f18570f`, revision `revisionproof-staging-00030-gnz`. Recheck live revision/configuration before deployment and retain a private service export.
- Use committed merged source and existing `cloudbuild.yaml`. Preserve `--gcs-source-staging-dir=gs://revisionproof-agentic-2026-kan-media/cloud-build-source`.
- Preserve existing runtime/build service accounts, resource limits, Gemini model/location, ClickHouse host, secret version references, and intelligence/read-only memory settings. No migrations, grant changes, or repository visibility changes are included.
- Revision replacement can invalidate process-local runs. Verification uses a separate QA session and stops before final delivery approval or memory save.

## Release procedure

1. Commit the scoped fixes, regression tests and review evidence; push the branch and open a PR against main.
2. Require both quality and isolated ClickHouse integration checks on the exact reviewed PR head to pass.
3. Merge without rewriting prior history, retain source and backup branches, and fast-forward local main.
4. Package the merged commit, verify archive integrity, submit the existing Cloud Build workflow, and record build/image/revision identities.
5. Check health/readiness/runtime settings, Studio/classic loading, and the three affected behaviors on the deployed service. Append concrete outcomes without representing local tests as LIVE provider execution.
