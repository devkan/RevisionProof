# RevisionProof engineering guardrails

- This product is a revision approval firewall, not a video editor.
- The only patch type in hackathon scope is `PUNCH_IN` with candidates 1.05x and 1.12x.
- Gemini may interpret feedback and suggest anchors, but deterministic code owns PASS/FAIL.
- Human approval freezes immutable canonical JSON plus its SHA-256 hash.
- Any `FAIL`, `ERROR`, or `NOT_CHECKED` verdict blocks publishing.
- Modes are `LIVE`, `FIXTURE`, `OFFLINE_REHEARSAL`, and `UNAVAILABLE`; never label fixture output as live.
- ClickHouse reads must go through the official `mcp-clickhouse` `run_query` tool in live mode.
- Media commands use fixed argument arrays, one process at a time, timeouts, and cleanup.
- Keep uploads at or below 24 MiB and 60 seconds; demo output is 1280x720 H.264/AAC.
