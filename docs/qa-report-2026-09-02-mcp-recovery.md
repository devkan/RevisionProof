# ClickHouse MCP recovery QA - 2026-09-02

Status: **PASS - deployed and verified on LIVE Cloud Run**

## Symptom and root cause

The user-visible run reached `NOTES_PARSED` through Vertex Gemini and then failed after about 64 seconds with `Live interpretation or evidence lookup failed`. The timing matched the two configured 30-second official MCP attempts plus process overhead. A separate LIVE run later completed the same query path, ruling out a persistent Gemini, credential, ClickHouse schema, or MCP-role failure.

The reader had a hard-coded two-attempt limit. A ClickHouse service returning from idle could therefore consume both fresh-process attempts before it became responsive.

## Fix

- Added `REVISIONPROOF_MCP_MAX_ATTEMPTS`, default `3`, bounded to `1..5`.
- Kept the 30-second timeout per attempt and the existing fresh `mcp-clickhouse` process for every retry.
- Added a warning with the current attempt and configured limit.
- Added regressions proving recovery after two timeouts and propagation after the third timeout.

Implementation commit: `4852259` (`fix(clickhouse): extend idle mcp recovery`).

## Local verification

- Backend: `104 passed in 56.58s`.
- Ruff check and format check: PASS.
- Frontend: 3 test files / 4 tests PASS; lint and production build PASS.
- Docker image: `revisionproof:mcp-retry-fix`, image ID `sha256:75a7b5d452d6051703283a621c68d6f112bee501abab1fa8b8afaacbc8be7915`, size 2,270,263,589 bytes.
- Temporary container on `127.0.0.1:18081`: `/health` returned `status=ok`; `/ready` returned `status=ready` in explicit `FIXTURE` mode. The temporary container was removed; no unrelated Docker resources were changed.

## Deployment evidence

- Account: `secureis@gmail.com`.
- Project: `revisionproof-agentic-2026-kan` (`348672234012`).
- Cloud Build source: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788338726.755047-7758a1b6f2ef4705862725a167e09763.tgz`.
- Cloud Build: `3ebc367e-31a4-4087-abba-6c245cb8c9bc`, SUCCESS in 7m24s.
- Image tag: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:3ebc367e-31a4-4087-abba-6c245cb8c9bc`.
- Image digest: `sha256:c7cd7fc4f9ebc19cbfbc37294fd42d8a79b3e1f9007715f9020a5911b8975cc5`.
- Cloud Run revision: `revisionproof-staging-00010-k4g`, 100% traffic.
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.

The guarded deployment verified the exact account, project ID, project number, project label, ClickHouse host, and numeric Secret Manager versions before submission. No other GCP project was selected or modified.

## Fresh gstack LIVE proof

Run `01M1GN7EY252SSM5F2AM170TKY` completed on the new revision:

- `POST /api/runs`: HTTP 201 in 51.878 seconds.
- Cloud Run log at `2026-09-02 17:55:13.686 +09:00`: `ClickHouse MCP timeout on attempt 1/3; retrying with a fresh process`.
- Trace: `INDEXED` -> `NOTES_PARSED` -> `EVIDENCE_ANCHORED`.
- Interpreter: `google.vertex.gemini`.
- Evidence: three matches from `mcp-clickhouse.run_query`.
- Raw state: `EVIDENCE_ANCHORED`, `retryable=false`, `error=null`.
- Runtime: `LIVE`, `live_ready=true`, no missing settings.
- Browser console: no errors.

This fresh run exercised the recovery path: the first 30-second MCP process timed out, the next fresh process succeeded, and the run reached evidence instead of the former failure state. The run stopped before preview rendering and made no new delivery approval.

Screenshot: `.gstack/qa-reports/screenshots/mcp-retry-live-pass-2026-09-02.png` (local QA artifact, intentionally gitignored).

## Remaining boundary

Three attempts improve recovery from a sleeping or transiently unavailable ClickHouse service but cannot guarantee recovery from a sustained outage. After the configured limit the API still fails closed. Run snapshots remain process-local, so a Cloud Run restart still requires a new run.
