# Architecture and trust boundaries

## Product boundary

RevisionProof is a revision approval firewall. It does not expose a timeline editor, arbitrary effects, XML/EDL export, collaboration, billing, or 4K processing in the hackathon build. The only generated patch is a centered `PUNCH_IN` at 1.05x or 1.12x for a 4–8 second evidence range.

## Runtime

One Cloud Run container serves the built React application and FastAPI API. Cloud Run accepts up to eight concurrent HTTP requests so the SSE trace does not block action requests, while a non-blocking application lock permits only one FFmpeg/OpenCV pipeline at a time. The hackathon deployment is capped at one 4 GiB instance. Live candidate media is copied to private GCS; the public media allowlist exposes only demo assets, A/B previews, and proof PNGs.

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
- Human approval is the only operation that creates a `RevisionSpec`; Pydantic freezes it and canonical content is SHA-256-addressed.
- The spec hash covers the exact CTA ROI, evidence ranges, and numerical thresholds used by later checks; loading a tampered spec fails validation.
- `OFFLINE_REHEARSAL` and `UNAVAILABLE` reject every state-changing request.
- `FAIL`, `ERROR`, `NOT_CHECKED`, missing integrations, malformed media, and command timeouts all block publishing.
- `Approve for Delivery` is a separate human action and is accepted only for a current `READY` proof.

## State machine

```text
INDEXED → NOTES_PARSED → EVIDENCE_ANCHORED → PREVIEWS_READY
→ HUMAN_APPROVED → VERSION_UPLOADED → VERIFYING → BLOCKED | READY

BLOCKED → VERSION_UPLOADED → VERIFYING → READY
any processing state → FAILED → retry at the last safe persisted boundary
```

## API

The OpenAPI contract is available at `/docs`. Core routes include `/api/runtime`, `/api/demo-assets`, `/api/runs`, resumable `/events`, `/previews`, `/approvals`, `/spec`, `/versions`, `/proof`, and `/delivery-approval`. Health and readiness probes are `/healthz` and `/readyz`.

## Hackathon durability boundary

ClickHouse audit tables are defined with append-only `MergeTree` engines; the current implementation writes frozen specs, version features, and checks. The API run snapshot and trace are still process memory, and full restart hydration of in-progress previews is not implemented. `max-instances=1` prevents cross-instance state splits but does not make memory durable; a Cloud Run restart requires starting a new run. This is a known live-spike gate, not a recovered-state claim.
