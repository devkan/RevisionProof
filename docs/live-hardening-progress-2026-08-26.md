# LIVE hardening progress, 2026-08-26

Status: **LIVE Cloud Run, Vertex Gemini, GCS, ClickHouse writer, and official MCP reader gates PASS. Final delivery approval intentionally remains pending.**

## Implemented

- Vertex defaults are locked to `global`, `gemini-3.5-flash-lite`, and `text-embedding-005`. Credential probes returned a Gemini response and a 768-dimensional embedding in project `revisionproof-agentic-2026-kan`.
- ClickHouse bootstrap creates append-only tables, exact writer/MCP roles, separate password users, and a deployment sentinel binding the GCP project ID to the ClickHouse Cloud host.
- The three former `ReplacingMergeTree` audit tables have a guarded, backup-preserving migration. Unknown and partial layouts fail closed.
- Official `mcp-clickhouse` compatibility requires the MCP user to keep `readonly=2`, `max_execution_time=5`, and `max_result_rows=2000`; a lower 50-row limit breaks the tool's internal settings discovery.
- GCS source and candidate uploads are create-only, use generation preconditions, and reuse an object only when SHA-256 metadata and size match.
- LIVE secrets are project-labeled, restricted to the runtime service account, selected by numeric version, and never written to tracked files.
- Cloud Build refuses placeholder hosts, non-global Vertex configuration, and zero/non-numeric secret versions. Cloud Run is public, capped at one instance, and configured for concurrency 4 so the resumable SSE stream cannot consume the only mutation slot.
- GCP runtime storage access is bucket-scoped `objectCreator + objectViewer`. The build account uses the 16-permission `revisionproofCloudRunDeployer` role; the former `objectAdmin` and `roles/run.admin` bindings were removed.
- CI installs the LIVE extras and runs a fresh ClickHouse 25.6 integration job covering schema convergence, adversarial role cleanup, official MCP view reads, and denial of base-table reads.

## Verification evidence

- Backend: 103 tests pass, including static GCP account/project/cleanup guard and SSE concurrency regression coverage.
- Frontend: 4 Vitest tests across three files pass; ESLint and Vite production build pass.
- Ruff check and format check pass for backend and scripts.
- All GCP Bash scripts pass `bash -n` and Dockerized ShellCheck.
- A fresh `revisionproof-ci-check` Compose volume passed append-only migration, excessive direct/inherited grant removal, official MCP `run_query`, and base-table denial. That disposable test volume was removed; the original `revisionproof` volume was preserved and restarted.
- Cloud Build and GitHub Actions YAML parse successfully.

## Final LIVE evidence

- Cloud Run: `revisionproof-staging-00009-mbh`, 100% traffic at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`.
- Final run: `01M0Z3338TYVHWHK4FZRGADTKZ`; interpreter `google.vertex.gemini`; evidence `mcp-clickhouse.run_query`.
- Human candidate gate: B, 1.12x, immutable spec hash `9153a52af2b90262d2b026070245204cd2b5449f49de2d3d18cc22bdeca1fed5`.
- Deterministic version gate: v2 `BLOCKED`, v3 `READY` with all three invariants passing.
- ClickHouse: 1 spec, 24 features, 6 checks for the final run. Bootstrap admin count 0; durable definer user count 1; durable view replicas 4; preserved backup count 1.
- GCS: private `revisionproof_v2_blocked.mp4` (394KB) and `revisionproof_v3_ready.mp4` (395KB) under the final run.
- Delivery approval: not executed; raw JSON remains `delivery_approved=false`.

The remaining engineering limit is process-local run state. `max-instances=1` avoids multi-instance split ownership but does not survive a restart. A restarted service requires a new run.
