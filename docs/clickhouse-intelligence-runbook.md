# ClickHouse intelligence runbook

Implementation date: 2026-09-03. Local SQL/UI and LIVE Cloud migration/deployment are verified. See the [release record](deployment-2026-09-03-clickhouse-intelligence.md) and [QA and inventory](qa-report-2026-09-03-clickhouse-intelligence.md). The public LIVE library is read-only; private owner-key setup remains a separate action.

## Try the UI locally

Use the normal README setup with `.env.example` copied to `.env`. The example enables `REVISIONPROOF_INTELLIGENCE_ENABLED=true`. Existing `.env` files must add this setting explicitly. Restart the backend after changing it.

The steps below exercise the **original scene-search demo** in the classic UI, not the default KANAPP Studio workflow. Select that alternate demo first. For the current Studio sample, use the [English walkthrough](demo-runbook.md). Local FIXTURE saving is rehearsal only; the public LIVE library remains read-only. Multi-edit recipes use their own storage/query path and the same private-save approval gates.

1. Review the default feedback and check the supported six-second punch-in.
2. Create A/B previews and choose B. The complete video is rendered and checked.
3. In **Revision Change Map**, choose a time window and **Compare this moment**. The larger original/revised players share play/pause and a seek slider; Escape closes the dialog.
4. Inspect the full video and the locked checks. Explicitly approve delivery, then select **Save approved edit**.
5. Start a new proof with similar feedback. **Approved Edit Memory** shows the earlier B choice as a reference; it does not check the request, choose B, or approve anything for you.
6. **Search engine and evidence** exposes the requested mode, actual engine, collection size, precision and request time. FIXTURE always says FIXTURE and is not a real vector benchmark.

The local rehearsal library resets on backend restart. LIVE memory is durable in ClickHouse, but the current run workspace remains process-local. A reload does not restore an active run.

## Database preparation

ClickHouse 26.2+ is required. QBit uses the 26.2-compatible Float32 layout; no 26.7-only functions are required. `docker compose -p revisionproof up -d clickhouse` initializes the twelve extension objects for a **new** volume. The additions include approved multi-edit recipes and seven-day smart-scene search rows; original media is never stored in these tables. Do not point a new image at another project's volume or use `down --volumes` on an existing project as an upgrade procedure. Export/backup an old 25.6 installation first. Use a separate named project/volume for testing.

Existing 26.2 volumes require the additive migration; Docker initialization scripts are not rerun for populated data directories. The migration has no DROP, DELETE, TRUNCATE or replacement of existing tables. It rejects unsupported versions, wrong engines and unsafe view definers. It is not an automatic repair tool for drifted schemas.

From the repository root, after installing the `live` extra:

```powershell
$env:PYTHONPATH='backend/src'
backend/.venv/Scripts/python.exe scripts/migrate_clickhouse_intelligence.py --host 127.0.0.1 --port 8123 --username revisionproof --confirm-host 127.0.0.1 --confirm-project local --insecure-local
```

This is dry-run. Add `--apply` only for the intended database. The password is prompted or supplied through `REVISIONPROOF_CLICKHOUSE_ADMIN_PASSWORD`; never pass production passwords as command arguments or commit them.

For Cloud, the exact target is:

- project `revisionproof-agentic-2026-kan`
- service `268999c1-badb-423e-993c-ebab14b551c4`
- host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`, TLS port 8443
- database `revisionproof`; preserve `segments_pre_seed_dedupe_20260826`

```powershell
backend/.venv/Scripts/python.exe scripts/migrate_clickhouse_intelligence.py --host r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud --confirm-host r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud --confirm-project revisionproof-agentic-2026-kan
```

The Cloud command checks the exact deployment sentinel before writes. Review `infra/clickhouse/intelligence.sql` and approve its narrowly scoped role grants before `--apply`. Alternatively, the signed-in SQL console can execute those reviewed statements **one at a time**, after the same sentinel check. Do not rerun the full historical bootstrap: the former bootstrap admin has been removed, and that workflow also changes credential assignments.

After migration, verify all twelve objects, their view definers, the smart-scene TTL and the MCP SELECT/denied-base-table boundaries. The parameterized neighbor views are necessary: on tested 26.2, an ordinary definer view prevented HNSW selection. Actual HNSW is reported only after EXPLAIN names the index. Small or selective queries may legitimately report exact. QBit is an alternative approximate-distance route, not a second HNSW index.

## Enable the Cloud UI

After migration, set `REVISIONPROOF_INTELLIGENCE_ENABLED=true` in the private `infra/gcp/live.env` used by `infra/gcp/deploy-live.sh`. The deploy script forwards a validated boolean to Cloud Build; the default remains false so old databases are not accidentally enabled. Every deployment must target the existing secureis account and exact project. Do not change another task's global gcloud defaults.

```bash
bash infra/gcp/deploy-live.sh infra/gcp/foundation.env infra/gcp/live.env revisionproof-agentic-2026-kan
```

This builds/deploys, so use only after the source checkpoint and approved migration are ready. A new run must prove Gemini interpretation, MCP retrieval, full render, MCP Change Map aggregation and matching persisted rows. Do not grant LIVE final delivery approval during autonomous QA.

The default public library is **read-only**. To allow owner-curated saves, the owner must configure a private 32+ character `REVISIONPROOF_MEMORY_WRITE_TOKEN`, preferably a separately approved Secret Manager secret with a pinned version and access restricted to the existing runtime service account. The current deploy script sets the two original ClickHouse secret bindings; an operator-added memory secret must be explicitly preserved/reapplied when deploying. Do not paste the key into feedback or documentation. Enter it only in the workspace-key field for an approved save. The browser clears it after submitting and never stores it in localStorage.

## Export before trial expiry

The code is not trial-limited. Hosting and stored Cloud data still depend on an active paid/trial service. Move/export data before expiry; neither Git nor an application deployment backs up ClickHouse. The billing screen on 2026-09-03 showed the trial credit period ending 2026-09-24; recheck this before acting.

Pause application writes first. Export only one workspace to a new, protected directory. Format v2 contains approved zoom memory, approved multi-edit recipes and raw Change Map measurements. Restore remains compatible with format v1 exports. It does **not** include seven-day smart-scene rows, existing audit tables, source/revised media in GCS, or in-progress runs. Keep separate ClickHouse/GCS backups for those.

```powershell
$env:PYTHONPATH='backend/src'
backend/.venv/Scripts/python.exe scripts/backup_clickhouse_intelligence.py export --host r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud --confirm-host r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud --confirm-project revisionproof-agentic-2026-kan --workspace revisionproof-demo --directory backups/revisionproof-intelligence-20260903
```

Files contain sensitive project metadata in plain text. Store securely and do not publish them. `backups/` is ignored by Git. Exclusive directory creation refuses overwriting an earlier/partial export. A completed manifest records SHA-256 hashes and row counts. Its absence means export is incomplete.

## Restore to a new 26.2+ service

Initialize the base schema, roles and intelligence schema on the dedicated destination. For a new Cloud service, independently establish the correct deployment sentinel and credentials first; do not copy the old host sentinel into a different service. Stop destination application writes throughout restoration. Do not run concurrent restore processes.

```powershell
backend/.venv/Scripts/python.exe scripts/backup_clickhouse_intelligence.py restore --host 127.0.0.1 --port 8123 --username revisionproof --confirm-host 127.0.0.1 --confirm-project local --insecure-local --workspace revisionproof-demo --directory backups/revisionproof-intelligence-20260903
```

Dry-run verifies all hashes, rows, columns, paths and workspace IDs, then requires empty target workspace rows in both raw tables and the aggregate table. Add `--apply` only after review. QBit/index data and materialized aggregation rebuild from raw inserts; platform-specific aggregate states are not copied. Each table's restored count is verified. A partial restore stops and is not blindly retried into populated tables; use a new empty destination or a separately reviewed recovery. The script never deletes existing data.

## Disable and remove later

First set `REVISIONPROOF_INTELLIGENCE_ENABLED=false` and redeploy the app. This hides the feature/stops extension work without deleting data or changing the original video workflow. Export data before any destructive cleanup.

Deletion is intentionally manual and requires separate approval: exact targets and dependency order are in the dated inventory. Never drop the database, preserved segment backup, shared roles, or the HOST NONE definer to remove this extension. Other projects must remain untouched.

## Reproduce the real vector check

`scripts/verify_intelligence_clickhouse.py` is restricted to loopback ports 18123 (dedicated QA container) or 8123 (isolated CI Compose project). It creates a clearly synthetic, timestamped benchmark namespace; never run it against Cloud. It checks exact/HNSW/QBit top-15 agreement on one 12,000-vector corpus, actual HNSW EXPLAIN selection, approved-recipe search, smart-scene search, duplicate-safe aggregation and denied MCP access to all three raw tables. This is a correctness smoke, not a representative performance/recall study.

```powershell
$env:PYTHONPATH='backend/src'
backend/.venv/Scripts/python.exe scripts/verify_intelligence_clickhouse.py --port 18123
```

The benchmark is now part of the isolated ClickHouse CI job. Existing images and volumes are preserved; cleanup must target only the named test resources.
