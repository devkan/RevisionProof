# Architecture and trust boundaries

## Product boundary

RevisionProof is a revision approval firewall. It does not expose a timeline editor, arbitrary effects, XML/EDL export, collaboration, billing, or 4K processing in the hackathon build. The only generated patch is a centered `PUNCH_IN` at 1.05x or 1.12x for a 4–8 second evidence range.

## Runtime

One Cloud Run container serves the built React application and FastAPI API. The deployed configuration uses concurrency 4 and a maximum of one 4 GiB instance. One instance matches the process-local run repository; four request slots allow the long-lived resumable SSE stream, a mutation, and supporting media requests to coexist. Concurrency 1 was rejected by LIVE QA because the SSE stream occupied the only slot and Cloud Run returned platform HTTP 429 for the next mutation. The public demo also caps new runs per minute, bounds the in-memory repository and idempotency ledger, and removes per-key async locks once all waiters exit. Live candidate media is created once in private GCS with SHA-256 metadata; an existing object is reused only when its hash and size match. The public media allowlist exposes only demo assets, A/B previews, and proof PNGs.

```text
Client note
   │
   ▼
Google ADK / Gemini ── interpretation only
   │
   ▼ embedding (768 dimensions)
mcp-clickhouse.run_query ── evidence view, top 5 → UI top 3
   │
   ▼
FFmpeg A/B previews ── 1.05x / 1.12x
   │
   ▼ human A/B selection
Immutable RevisionSpec JSON + SHA-256
   │
   ▼ full-source FFmpeg render
FFmpeg/OpenCV deterministic feature extraction
   │
   ├── direct ClickHouse INSERT (audit facts)
   ├── mcp-clickhouse.run_query (version feature diff view)
   │         └── Python reapplies frozen manifest thresholds → PASS/FAIL
   ├── private GCS version object (durable audit artifact)
   └── generated MP4 returned for review and download
```

The primary path is server-owned: selecting A or B renders and verifies the complete source automatically. `/versions` remains a secondary path for checking a full MP4 produced by an external editor or tool; it is not required to complete the normal demo.

## Trust boundaries

- Gemini may turn natural language into structured intent. It never returns a verification verdict.
- The fixture interpreter and segment index use explicit `fixture.*` source names.
- Live ClickHouse reads use only approved views through the official MCP tool: `search_segments`, `version_feature_diff`, and (when the intelligence extension is enabled) `revision_change_map`, `approved_edit_memory`, and `approved_edit_neighbors`.
- ClickHouse writes use a separate insert-only credential.
- ClickHouse provisioning records exactly one deployment sentinel containing the dedicated GCP project ID and ClickHouse Cloud host. Bootstrap, cloud migration, and cleanup refuse a mismatch.
- Human approval is the only operation that creates a `RevisionSpec`; Pydantic freezes it and canonical content is SHA-256-addressed.
- The spec hash covers the exact CTA ROI, evidence ranges, and numerical thresholds used by later checks; loading a tampered spec fails validation.
- `OFFLINE_REHEARSAL` and `UNAVAILABLE` reject every state-changing request.
- `FAIL`, `ERROR`, `NOT_CHECKED`, missing integrations, malformed media, and command timeouts all block publishing.
- `Approve for Delivery` is a separate human action and is accepted only for a current `READY` proof.
- Mutation routes accept bounded `Idempotency-Key` headers and reject reuse with a different request fingerprint. Version uploads additionally require a browser-computed `X-Content-SHA256`; the server hashes the received stream and binds the idempotency fingerprint to that verified digest. Idempotency records share the process-local durability boundary below.

## Optional ClickHouse intelligence

Decoded source/revised frames (2 samples/second) and one-second audio levels enter append-only `revision_frame_pairs`. A security-definer materialized view populates `revision_change_windows` (`AggregatingMergeTree`). `uniqExactState(sample_ms)` and max aggregates make duplicate retries insensitive to repeated samples. The MCP-only `revision_change_map` view merges states across parts. Python labels each second requested/unchanged/review, and the UI opens synchronized video comparison. Diagnostics cannot alter frozen spec thresholds or the existing verdict.

Only an all-PASS proof with explicit final delivery approval and a matching, available Change Map without review flags can be saved. An additional private workspace key gates LIVE saves. Saved intent, safe crop parameters, model-tagged normalized 768D embedding, spec hash and proof are append-only; media URLs are excluded. The human approval event remains a separate audit fact. The public library is not a multi-tenant authorization system and must contain non-sensitive, licensed demo edits only.

Memory reads are exact L2, HNSW, or `L2DistanceTransposed` against materialized `QBit(Float32, 768)`. The HNSW route uses a parameterized definer view containing the distance ordering and fixed limit; ClickHouse 26.2 did not optimize the same search through an ordinary definer view. `EXPLAIN indexes=1` must name `approved_edit_hnsw` before the response reports actual HNSW. No index selection or a small collection means explicit exact fallback. Match IDs are deduplicated, similarity below 0.55 is discarded in LIVE, and the top three references never auto-approve an edit.

Export/restore includes source extension tables, not aggregate-state serialization. QBit and the materialized view rebuild during restore. Stop writes during the export/restore maintenance window. Existing workspace data is never overwritten by the restore tool. See [the runbook](clickhouse-intelligence-runbook.md).

## State machine (unchanged)

```text
INDEXED → NOTES_PARSED → EVIDENCE_ANCHORED → PREVIEWS_READY
→ HUMAN_APPROVED → VERSION_UPLOADED → VERIFYING → BLOCKED | READY

BLOCKED → VERSION_UPLOADED → VERIFYING → READY
LIVE interpretation/evidence failure → FAILED → retry preserved source feedback
version verification failure → FAILED → retry upload from the frozen approved spec
```

## API

The OpenAPI contract is available at `/docs`. Core routes include `/api/runtime`, `/api/demo-assets`, `/api/runs`, resumable `/events`, `/previews`, `/approvals`, `/automatic-version`, `/generated-video`, `/spec`, the secondary `/versions` upload, `/proof`, and `/delivery-approval`. Cloud Run-safe health and readiness routes are `/health` and `/ready`; the legacy `z`-suffixed aliases remain for local compatibility only because Cloud Run reserves some paths ending in `z`.

## Hackathon durability boundary

ClickHouse audit tables are defined with append-only `MergeTree` engines; the implementation writes frozen specs, version features, and checks. Schema migration preserves the former segment data in `revisionproof.segments_pre_seed_dedupe_20260826` and refuses unknown or partial layouts. The API run snapshot and trace are still process memory, and full restart hydration of in-progress previews is not implemented. Cloud Run service-level `--max=1` prevents simultaneous split ownership but does not make memory durable; a Cloud Run restart requires starting a new run. The preserved feedback retry works only while that process remains alive. This is a known hackathon boundary, not a recovered-state claim.
