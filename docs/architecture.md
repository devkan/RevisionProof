# Architecture and trust boundaries

## Product boundary

RevisionProof combines bounded video edits with human approval and deterministic export verification. The owner expanded the hackathon scope on 2026-09-03 to center zoom, literal text overlays, timed subtitle cues, exact interval cuts, and reviewed silence removal. Sources remain MP4/MOV/WebM, <=24 MiB, 4–60 seconds; prepared media is aspect-preserving 1280×720, 30 fps H.264/AAC. There are at most 24 operations and at least one output second. Auto-transcription, object/background manipulation, generation and removal of burned-in text are outside scope.

See [current usage and release evidence](basic-editing-guide-2026-09-03.md) and [engineering review](basic-editing-plan-2026-09-03.md). The original scene-search proof remains an explicit alternate demo; its legacy PUNCH_IN contracts and 4–8 second previews retain their behavior.

## Runtime and editing path

A Cloud Run container serves React and FastAPI with one 4 GiB / 2 CPU instance and concurrency 4. Media jobs are serialized; SSE and supporting requests can coexist. Runs are process-local, bounded and rate-limited. A restart requires a new run. Private GCS stores verified version objects; ClickHouse stores append-only facts. Originals and previews are not recovered after restart.

```text
User edit controls OR natural-language draft (LIVE Google ADK/Gemini)
  -> explicit editable plan: original times, literal words, positions
  -> normalized original + per-channel silence analysis
  -> user selects operations and proposed cuts
  -> FFmpeg full previews (A/B appearance; cut-only gets A)
  -> human choice freezes spec 3.0 + full-preview SHA-256
  -> copy approved preview to export
  -> exact identity + mapped kept scenes + approved audio checks
  -> ClickHouse INSERT -> official MCP feature diff -> frozen thresholds
  -> private GCS artifact + Change Map + user playback
  -> separate final human delivery approval
```

All operations use original time. Frame-aligned cuts merge into kept spans; source time maps from output time for verification and synchronized browser comparison. Text is rasterized using Pillow and a bundled Korean/English font into PNG layers; user strings never enter FFmpeg expressions. All zoom filters are applied before text overlays, then both picture and audio are trimmed by identical boundaries and concatenated. Silence detection uses the maximum per-channel RMS over 20ms blocks, preserving 0.12s margins. Proposed cuts require explicit selection; surplus proposals are bounded and explained.

New EDIT_PLAN candidates use spec 3.0. The approved full preview is hashed and rechecked at use. Export is byte-identical, so short or small missing text cannot slip through sampled frame checks. Kept, unedited scenes compare against mapped original frames, while intended visual changes compare against the approved reference. Audio levels compare against the approved cut timeline. The existing three ClickHouse check IDs remain compatible; the feature-diff baseline is labelled `approved-reference`, not legacy `v1`. Change Map remains sampled diagnostics, not a semantic or every-frame verdict.

Legacy spec 2.0 retains CTA/absolute audio limits, 2.1 retains uploaded full-video/absolute audio limits, and 2.2 retains original-relative audio RMS/peak deltas. Their original canonical JSON/hash is covered by pinned pre-expansion fixtures. The external-editor verification UI remains available only for the legacy approximate-check contract; new plans require the exact approved export.

Guided controls report `user.structured`. Natural language returns a reviewable draft and warnings, never executable commands or approval. Ambiguity preserves input and the manual controls. The edit library currently accepts only legacy zoom proofs, so multi-edit save is rejected rather than encoded as a false zoom.

## Trust boundaries

- Gemini may turn natural language into structured intent. It never returns a verification verdict.
- The fixture interpreter and segment index use explicit `fixture.*` source names.
- Live ClickHouse reads use only approved views through the official MCP tool: `search_segments`, `version_feature_diff`, and (when the intelligence extension is enabled) `revision_change_map`, `approved_edit_memory`, and `approved_edit_neighbors`.
- ClickHouse writes use a separate insert-only credential.
- ClickHouse provisioning records exactly one deployment sentinel containing the dedicated GCP project ID and ClickHouse Cloud host. Bootstrap, cloud migration, and cleanup refuse a mismatch.
- Human approval is the only operation that creates a `RevisionSpec`; Pydantic freezes it and canonical content is SHA-256-addressed.
- The spec hash covers the visual-lock kind, ROI, evidence ranges, and numerical thresholds used by later checks; loading a tampered spec fails validation.
- `OFFLINE_REHEARSAL` and `UNAVAILABLE` reject every state-changing request.
- `FAIL`, `ERROR`, `NOT_CHECKED`, missing integrations, malformed media, and command timeouts all block publishing.
- `Approve for Delivery` is a separate human action and is accepted only for a current `READY` proof.
- Mutation routes accept bounded `Idempotency-Key` headers and reject reuse with a different request fingerprint. Source and version uploads additionally require a browser-computed `X-Content-SHA256`; the server hashes the received stream and binds the idempotency fingerprint to that verified digest. Source fingerprints also bind feedback and the selected range. Idempotency records share the process-local durability boundary below.

## Optional ClickHouse intelligence

Decoded source/revised frames (2 samples/second) and one-second audio levels enter append-only `revision_frame_pairs`. A security-definer materialized view populates `revision_change_windows` (`AggregatingMergeTree`). `uniqExactState(sample_ms)` and max aggregates make duplicate retries insensitive to repeated samples. The MCP-only `revision_change_map` view merges states across parts. Python labels each second requested/unchanged/review, and the UI opens synchronized video comparison. Diagnostics cannot alter frozen spec thresholds or the existing verdict.

Only an all-PASS proof with explicit final delivery approval and a matching, available Change Map without review flags can be saved. An additional private workspace key gates LIVE saves. Saved intent, safe crop parameters, model-tagged normalized 768D embedding, spec hash and proof are append-only; media URLs are excluded. The human approval event remains a separate audit fact. The public library is not a multi-tenant authorization system and must contain non-sensitive, licensed demo edits only.

Memory reads are exact L2, HNSW, or `L2DistanceTransposed` against materialized `QBit(Float32, 768)`. The HNSW route uses a parameterized definer view containing the distance ordering and fixed limit; ClickHouse 26.2 did not optimize the same search through an ordinary definer view. `EXPLAIN indexes=1` must name `approved_edit_hnsw` before the response reports actual HNSW. No index selection or a small collection means explicit exact fallback. Match IDs are deduplicated, similarity below 0.55 is discarded in LIVE, and the top three references never auto-approve an edit.

Search is lazy: creating or interpreting a run no longer waits for approved-memory retrieval. Opening the optional “Past approved edits” area fetches references. A zero-count LIVE library returns `actual_engine: "none"`, with no embedding/vector query. The empty UI explains the runtime save policy and hides engine controls; a populated library retains advanced search details.

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

The OpenAPI contract is available at `/docs`. Core routes include `/api/runtime` (including upload limits), `/api/demo-assets`, `/api/edit-plans/interpret`, `/api/runs`, `/api/runs/upload`, and run-scoped `/source-video`, resumable `/events`, `/previews`, `/approvals`, `/automatic-version`, `/generated-video`, `/spec`, the secondary `/versions` upload, `/proof`, and `/delivery-approval`. Cloud Run-safe health and readiness routes are `/health` and `/ready`; the legacy `z`-suffixed aliases remain for local compatibility only because Cloud Run reserves some paths ending in `z`.

## Hackathon durability boundary

ClickHouse audit tables are defined with append-only `MergeTree` engines; the implementation writes frozen specs, version features, and checks. Schema migration preserves the former segment data in `revisionproof.segments_pre_seed_dedupe_20260826` and refuses unknown or partial layouts. The API run snapshot and trace are still process memory, and full restart hydration of in-progress previews is not implemented. Cloud Run service-level `--max=1` prevents simultaneous split ownership but does not make memory durable; a Cloud Run restart requires starting a new run. The preserved feedback retry works only while that process remains alive. This is a known hackathon boundary, not a recovered-state claim.

Normalized source uploads live under `runtime/runs/<run_id>/source/source.mp4`; they are not added to the public demo catalog or durably archived to GCS by this change. Their route resolves through the existing in-memory run, returns private/no-store caching, and becomes unavailable when the run is evicted or the process restarts. Feedback retry reuses the same prepared source and selected range while the run remains alive.
