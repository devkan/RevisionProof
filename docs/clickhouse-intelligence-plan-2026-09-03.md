# ClickHouse revision intelligence implementation

Status: implementation, local verification, GitHub push, additive Cloud migration and LIVE deployment/QA complete. User approved Change Map + Approved Edit Memory + HNSW + optional QBit on 2026-09-03, then requested push/deployment. See the [release record](deployment-2026-09-03-clickhouse-intelligence.md), [QA/inventory](qa-report-2026-09-03-clickhouse-intelligence.md) and [runbook](clickhouse-intelligence-runbook.md). Public memory is intentionally read-only until separate owner-key setup.

## Scope and order

- [x] Check handoff, current runtime, schema, security boundaries and official ClickHouse documentation.
- [x] Add append-only frame measurements, one-second materialized aggregation, memory table and guarded migration.
- [x] Add sampled visual/audio Change Map and verified memory retrieval/storage APIs.
- [x] Add readable, accessible timeline comparison and memory recommendations to the existing workspace.
- [x] Exercise exact/HNSW/QBit against isolated Docker ClickHouse 26.2; preserve old volumes.
- [x] Run backend/frontend tests, gstack browser/design checks and scoped code review; document evidence.
- [x] Apply the additive Cloud migration and redeploy the dedicated RevisionProof service; verify fresh LIVE render, persisted measurements and browser behavior.

## Contracts

Change Map compares decoded source/revision pairs at 2 samples/second, aggregates by second in ClickHouse, and displays requested change, unchanged, or review-needed. It is sampled diagnostic evidence, not an assertion that every frame is identical. Existing frozen three-check verdicts stay authoritative. Timeline selection opens synchronized, enlarged original/revised playback.

Memory stores normalized intent, safe candidate parameters, embedding-model identity, immutable spec hash, passed proof and final human approval. Never learn from A/B selection alone. Never store public video URLs (GCS lifecycle can expire). One server-owned workspace namespace is used; it is not tenant authentication. The public deployment is read-only by default. A separate explicit save action requires an operator token in LIVE mode; local FIXTURE storage is visibly labelled and process-local. No automatic final delivery approvals during LIVE QA.

Search supports exact / HNSW / QBit. HNSW is the preferred indexed route; small collections use exact search. Actual selected index is checked with EXPLAIN rather than inferred from configuration. QBit uses normalized 768-dimensional Float32 vectors with the 26.2-compatible L2DistanceTransposed function; it is an alternative route, not a second index stacked on HNSW. Similarity is not a probability. Recommendations never replace fresh evidence or auto-select an edit.

All LIVE reads go through official mcp-clickhouse. Writer remains insert-only. New views use the existing HOST NONE definer. Schema migration must validate the exact deployment sentinel and preserve revisionproof.segments_pre_seed_dedupe_20260826. Cloud and local Docker both use ClickHouse 26.2-compatible SQL. No changes to other projects or global gcloud defaults.

## Verification and rollback

Test empty/error/search modes; malformed vectors; workspace scoping; duplicate inserts; partial map coverage; changed frames inside/outside requested ranges; audio drift; approval/save authorization; mobile/keyboard/contrast/loading states. Test real SQL, view grants and index plans, not only SQL-string mocks. Compare QBit and HNSW top-k to exact in an isolated, labelled benchmark corpus.

Add an explicit backup/export and restore path with manifests and content hashes, plus additive resource inventory. Application feature flags can disable the extension without deleting data. Cloud data is not guaranteed to survive trial expiry: export or arrange paid hosting before then.

## References

- https://clickhouse.com/docs/engines/table-engines/mergetree-family/annindexes
- https://clickhouse.com/docs/sql-reference/data-types/qbit
- https://clickhouse.com/blog/clickhouse-release-26-02
