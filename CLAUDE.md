# RevisionProof engineering guardrails

- This product combines bounded video edits with an approval and verification workflow.
- The owner expanded scope on 2026-09-03: center zoom, literal text overlays, timed subtitle cues, explicit time cuts, and user-selected silence cuts. See `docs/basic-editing-plan-2026-09-03.md`.
- Legacy `PUNCH_IN` specs 2.x remain compatible. New `EDIT_PLAN` specs 3.0 freeze the selected original-time operations, mapped output timeline and full-preview SHA-256.
- New-plan exports must be byte-identical copies of the approved preview. They do not accept approximate external re-encodes as approved exports.
- Keep no more than 24 operations and at least one output second. Silence detection proposes cuts; the user selects them before rendering. All channels must be quiet.
- LIVE Gemini can draft editable subtitle cues from Korean, English, or mixed speech; users review names and wording before rendering. Object tracking/removal, generated scenes, background replacement and removal of burned-in text remain outside scope.
- Gemini may interpret feedback and suggest anchors, but deterministic code owns PASS/FAIL.
- Human approval freezes immutable canonical JSON plus its SHA-256 hash.
- Any `FAIL`, `ERROR`, or `NOT_CHECKED` verdict blocks publishing.
- Modes are `LIVE`, `FIXTURE`, `OFFLINE_REHEARSAL`, and `UNAVAILABLE`; never label fixture output as live.
- ClickHouse reads must go through the official `mcp-clickhouse` `run_query` tool in live mode.
- Media commands use fixed argument arrays, one process at a time, timeouts, and cleanup.
- Keep uploaded files at or below 32,000,000 bytes (shown as 32 MB) and 60 seconds so the multipart request remains below Cloud Run's 32 MiB HTTP/1 limit; demo output is 1280x720 H.264/AAC.
