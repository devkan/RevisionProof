# Architecture and trust boundaries

## Product boundary

RevisionProof is a revision approval firewall. It does not expose a timeline editor, arbitrary effects, XML/EDL export, collaboration, billing, or 4K processing in the hackathon build. The only generated patch is a centered `PUNCH_IN` at 1.05x or 1.12x for a 4–8 second evidence range.

## Runtime

One Cloud Run container serves the built React application and FastAPI API. The guarded deployment configuration uses concurrency 1 and a maximum of one 4 GiB instance, matching the process-local run repository and single FFmpeg/OpenCV pipeline. The currently deployed historical FIXTURE revision still records concurrency 8 in its dated inventory; a new build is required to apply the source configuration. The public demo also caps new runs per minute, bounds the in-memory repository and idempotency ledger, and removes per-key async locks once all waiters exit. Live candidate media is created once in private GCS with SHA-256 metadata; an existing object is reused only when its hash and size match. The public media allowlist exposes only demo assets, A/B previews, and proof PNGs.

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
   ▼ human approval
Immutable RevisionSpec JSON + SHA-256
   │
   ▼ version upload
FFmpeg/OpenCV deterministic feature extraction
   │
   ├── direct ClickHouse INSERT (audit facts)
   ├── mcp-clickhouse.run_query (version feature diff view)
   │         └── Python reapplies frozen manifest thresholds → PASS/FAIL
   └── GCS version object
```

## Trust boundaries

- Gemini may turn natural language into structured intent. It never returns a verification verdict.
- The fixture interpreter and segment index use explicit `fixture.*` source names.
- Live ClickHouse reads use only the `search_segments` and `version_feature_diff` views through the official MCP tool.
- ClickHouse writes use a separate insert-only credential.
- ClickHouse provisioning records exactly one deployment sentinel containing the dedicated GCP project ID and ClickHouse Cloud host. Bootstrap, cloud migration, and cleanup refuse a mismatch.
- Human approval is the only operation that creates a `RevisionSpec`; Pydantic freezes it and canonical content is SHA-256-addressed.
- The spec hash covers the exact CTA ROI, evidence ranges, and numerical thresholds used by later checks; loading a tampered spec fails validation.
- `OFFLINE_REHEARSAL` and `UNAVAILABLE` reject every state-changing request.
- `FAIL`, `ERROR`, `NOT_CHECKED`, missing integrations, malformed media, and command timeouts all block publishing.
- `Approve for Delivery` is a separate human action and is accepted only for a current `READY` proof.
- Mutation routes accept bounded `Idempotency-Key` headers and reject reuse with a different request fingerprint. Version uploads additionally require a browser-computed `X-Content-SHA256`; the server hashes the received stream and binds the idempotency fingerprint to that verified digest. Idempotency records share the process-local durability boundary below.

## State machine

```text
INDEXED → NOTES_PARSED → EVIDENCE_ANCHORED → PREVIEWS_READY
→ HUMAN_APPROVED → VERSION_UPLOADED → VERIFYING → BLOCKED | READY

BLOCKED → VERSION_UPLOADED → VERIFYING → READY
LIVE interpretation/evidence failure → FAILED → retry preserved source feedback
version verification failure → FAILED → retry upload from the frozen approved spec
```

## API

The OpenAPI contract is available at `/docs`. Core routes include `/api/runtime`, `/api/demo-assets`, `/api/runs`, resumable `/events`, `/previews`, `/approvals`, `/spec`, `/versions`, `/proof`, and `/delivery-approval`. Cloud Run-safe health and readiness routes are `/health` and `/ready`; the legacy `z`-suffixed aliases remain for local compatibility only because Cloud Run reserves some paths ending in `z`.

## Hackathon durability boundary

ClickHouse audit tables are defined with append-only `MergeTree` engines; the current implementation writes frozen specs, version features, and checks. Schema migration preserves the three former `ReplacingMergeTree` tables as backups and refuses unknown or partial layouts. The API run snapshot and trace are still process memory, and full restart hydration of in-progress previews is not implemented. Cloud Run service-level `--max=1` prevents cross-revision state splits but does not make memory durable; a Cloud Run restart requires starting a new run. The preserved feedback retry works only while that process remains alive. This is a known live-spike gate, not a recovered-state claim.
