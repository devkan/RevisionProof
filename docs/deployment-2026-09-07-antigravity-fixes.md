# Antigravity QA fixes: integration and release

Date: 2026-09-07 KST. Status: **Completed: PR #2 merged, deployed, and all three affected behaviors verified on the live service.**

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

## Execution identities

- Fix/evidence commit: `dae8033e8d4ada1a39f4da6569c5fe4b572c11c1`.
- [PR #2](https://github.com/devkan/RevisionProof/pull/2) merged with merge commit `b13d8b0e2a1e20e6fb51afdc06e281bb03ea34c3`. Its Git tree exactly matches the tested PR head. Local main was fast-forwarded; source and backup branches remain.
- [PR CI 34119684596](https://github.com/devkan/RevisionProof/actions/runs/34119684596): quality and ClickHouse integration both succeeded before merge. Hosted quality results include backend **353 passed**, frontend **78 passed / 16 files**, lint/format, three release-gate rehearsals and the complete container build.
- [Merged-main CI 34120899603](https://github.com/devkan/RevisionProof/actions/runs/34120899603) runs against `b13d8b0`; final result below.
- Source ZIP: `runtime/revisionproof-deploy-b13d8b0.zip`, **10,960,376 bytes**; SHA-256 `0433ab1c74f43577bc10840692be06378773384c5893eeb8681d4463f1e538d4`. Uploaded to the existing Cloud Shell home directory and verified before exclusive extraction.
- Fresh preflight confirmed previous revision `revisionproof-staging-00030-gnz` at 100% traffic. Private pre/post service exports and Cloud Build JSON are retained in Cloud Shell `/home/secureis/revisionproof-release-20260907-qa-fixes/`.
- [Cloud Build 44079831-b9b3-4f90-9f01-dee3deb3ac46](https://console.cloud.google.com/cloud-build/builds/44079831-b9b3-4f90-9f01-dee3deb3ac46?project=348672234012), created `2026-09-07T12:17:28Z` (21:17 KST), uses the unchanged LIVE build workflow.
- Source staging object: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788783437.125324-51c218f35a3f497eb627ca655c514af9.tgz`.

## Deployment and service verification

- Cloud Build **SUCCESS**, finished `2026-09-07T12:22:57Z` (21:22 KST).
- New revision: **`revisionproof-staging-00031-5bl`**, Ready / ConfigurationsReady / RoutesReady all True, **100% traffic**.
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:44079831-b9b3-4f90-9f01-dee3deb3ac46`.
- Image digest: `sha256:fe5b824aa26e3d835e33ef357b76ed9a25cff14a12440a43c5cbc36180de8160`. The deployed revision's resolved digest matches Cloud Build's pushed image.
- Before/after comparison passed: environment values, secret names/versions, resources, container ports, concurrency, timeout, runtime service account, min/max scaling unchanged. Public memory still read-only; no memory write token configured.
- Merged-main CI **34120899603 SUCCESS**, both quality and ClickHouse integration passed on the merged source.
- At `2026-09-07T12:23:56Z`, `/health`, `/ready`, `/api/runtime`, `/studio`, and `/` all returned **HTTP 200**. Runtime LIVE, missing settings `[]`, intelligence enabled, memory policy `read_only`.
- Studio/classic HTML serves `index-mB8AWTRx.js` and `index-BaYy-LUs.css`, matching the verified frontend build.
- Readiness proves configured credentials, not fresh provider execution: `integration_execution_verified=false` remains the endpoint's explicit boundary. Run-level behavior results are recorded separately below.

Rollback, only if needed and authorized by the release context: route this existing service back to `revisionproof-staging-00030-gnz` using `gcloud run services update-traffic revisionproof-staging --project=revisionproof-agentic-2026-kan --region=us-central1 --to-revisions=revisionproof-staging-00030-gnz=100`. No rollback was needed or executed.

## Affected-behavior QA on the deployed service

One separate browser QA run, `01M1XX9TGX9DZQG5MPD2Y7E3EB`, used the existing 30-second Kanapp source, zoom plus the original long English test sentence at 4–10 seconds, and selected candidate B. These are fresh deployment results, separate from Antigravity's earlier reproduction and local regression tests.

| Check | Observed result |
| --- | --- |
| A: English word wrapping | Actual deployed B preview frame at 5 seconds keeps `professionals.` intact on its third line; `automated-verification` also remains intact. [Rendered evidence](evidence-release-20260907-caption-live.png). |
| B: Failed external video comparison | Uploading the unchanged original as an external edit produced BLOCKED / 1 of 3 checks pass / 6 review seconds, with `generated_version_url=null`. Selected 0:05–0:06; Compare this moment was enabled. The dialog loaded the source and the actual external blob URL; both players had readyState 4, no media error, and played at 5.216672 / 5.216673 seconds. |
| C: BLOCKED to PASS details | With the failed 0:05–0:06 window selected, Run checks again generated and checked B on the same Studio page without reloading. Result READY / 3 of 3 PASS / 0 review flags. The detail immediately became 0:04–0:05 Requested edit; the prior failure explanation and 7.82% residual were replaced with the current explanation and 0.00%. No stale failure detail node remained. |
| Live diagnostic source | Both maps report `mcp-clickhouse.run_query`, 60 frame pairs. BLOCKED analysis `01M1XXG2T3TDJFJJQHZBHKAJY6`; PASS analysis `01M1XXKR7TDK0ZV1XE3KZM0GTR`. |
| Approval boundary | `delivery_approved=false` after all checks. No final delivery approval or memory save was performed. |
| Browser/service | Studio console had no observed errors or warnings. Classic loaded with enabled upload controls and no errors/warnings after retry. Final HTTP checks at `12:33:01Z` returned 200 on all five routes. |

[Structured results and HTTP evidence](evidence-release-20260907-results.json). Full run snapshots and the downloaded B preview remain in ignored `runtime/release-20260907-qa-fixes/`.

The regenerated PASS applies to the new approved B output, not to the earlier wrong external upload. This run verifies the bounded edit/check/ClickHouse path; it does not claim fresh speech transcription, scene search, exhaustive semantic analysis, or final delivery approval.

## Operational observation and final bookkeeping

During external verification, a separate Classic navigation returned HTTP 429 at `12:29:15Z`. Cloud Run logged that no instance was available. This occurred with the preserved single-instance/concurrency-4 configuration. After the active check finished, Classic reloaded normally and all final HTTP checks returned 200. This release makes no scaling change; handling overlapping long-running requests remains an operational follow-up if concurrent use is required.

The application source deployed is `b13d8b0`; the subsequent release-record commit changes only documentation/evidence. Existing source/backup branches and private repository visibility are preserved. No application-code changes were needed after the accepted Antigravity re-review.

## Closing handoff check

- Latest pushed release-record commit: `a04b70bb58365834c33cb26d60f777486956e95e`; local and remote main match, and GitHub reports no open PRs.
- [Final release-record CI 34122820916](https://github.com/devkan/RevisionProof/actions/runs/34122820916) is completed / SUCCESS on head `a04b70bb58365834c33cb26d60f777486956e95e`; both quality and ClickHouse integration passed. This closed the final release check.
- Handoff-only checks: `/health` and `/ready` returned HTTP 200 / LIVE; the retained Studio page showed Full video passed, no sampled review flags, updated requested-edit detail, and 0.00% residual. Existing browser workspace was preserved without reload or mutation.

## Final Documentation Harmonization Note (2026-09-08)

- **Deployed Application Code**: Remains strictly **`b13d8b0`** on Cloud Run revision **`revisionproof-staging-00031-5bl`**.
- **Documentation Updates**: Subsequent documentation commits (including release-record commit `a04b70b` and the 2026-09-08 Antigravity final documentation synchronization) update only user-facing documentation (`README.md`, `HANDOFF.md`, `docs/README.md`, `docs/submission-pack-2026-08-27.md`, and this record).
- **No Application Re-Deployment**: These documentation changes do not alter application source code, dependencies, or container images. No new container build or Cloud Run deployment is triggered or required. The active running service remains revision `revisionproof-staging-00031-5bl`.
