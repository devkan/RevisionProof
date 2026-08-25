# Architecture and trust boundaries

## Product boundary

RevisionProof is a revision approval firewall. It does not expose a timeline editor, arbitrary effects, XML/EDL export, collaboration, billing, or 4K processing in the hackathon build. The only generated patch is a centered `PUNCH_IN` at 1.05x or 1.12x for a 4–8 second evidence range.

## Runtime

One Cloud Run container serves the built React application and FastAPI API. FFmpeg and OpenCV run inside the container with concurrency fixed to one. Live media is copied to GCS; the local filesystem is temporary working storage.

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
FFmpeg/OpenCV deterministic checks ── sole PASS/FAIL owner
   │
   ├── direct ClickHouse INSERT (audit facts)
   ├── mcp-clickhouse.run_query (version feature diff view)
   └── GCS version object
```

## Trust boundaries

- Gemini may turn natural language into structured intent. It never returns a verification verdict.
- The fixture interpreter and segment index use explicit `fixture.*` source names.
- Live ClickHouse reads use only the `search_segments` and `version_feature_diff` views through the official MCP tool.
- ClickHouse writes use a separate insert-only credential.
- Human approval is the only operation that creates a `RevisionSpec`; Pydantic freezes it and canonical content is SHA-256-addressed.
- `FAIL`, `ERROR`, `NOT_CHECKED`, missing integrations, malformed media, and command timeouts all block publishing.

## State machine

```text
INDEXED → NOTES_PARSED → EVIDENCE_ANCHORED → PREVIEWS_READY
→ HUMAN_APPROVED → VERSION_UPLOADED → VERIFYING → BLOCKED | READY

BLOCKED → VERSION_UPLOADED → VERIFYING → READY
any processing state → FAILED → retry at the last safe persisted boundary
```

## API

The OpenAPI contract is available at `/docs`. Core routes are `/api/demo-assets`, `/api/runs`, `/api/runs/{id}/events`, `/previews`, `/approvals`, `/spec`, `/versions`, and `/proof`. Health and readiness probes are `/healthz` and `/readyz`.
