# Security and failure policy

- Uploads accept MP4 only, at most 24 MiB and 60 seconds, with H.264 video, AAC audio, and 1280x720 dimensions.
- Media commands are argument arrays, never shell-composed strings. A non-blocking pipeline lock permits one render/verification workflow at a time, and timed-out commands remove partial outputs.
- Public media routes allow only bundled demos, A/B previews, and CTA proof PNGs. Uploaded candidate versions and arbitrary runtime paths return 404.
- Run and version identifiers are validated before SQL is built. Embeddings must have exactly 768 numeric values and query limits are bounded.
- The MCP ClickHouse credential receives SELECT only on two views. The writer credential receives INSERT only.
- Reader and writer usernames/passwords are separate settings; assign `revisionproof_mcp_reader` and `revisionproof_writer` as their default roles during ClickHouse provisioning.
- Secrets enter Cloud Run through Secret Manager; they are not committed or returned by the API.
- A proof allows publishing only when every deterministic check is `PASS`. Empty checks, unavailable checks, exceptions, or integration failures are blocked.
- Revision specs are frozen after approval. A new approval requires a new run and hash.
- Revision spec validation recomputes the canonical hash and binds the approved time range, locked ranges, ROI, and threshold keys.
- `FIXTURE`, `OFFLINE_REHEARSAL`, `LIVE`, and `UNAVAILABLE` are user-visible execution modes; the latter two non-live modes reject state-changing requests.
- The container runs as an unprivileged UID. Cloud Run is capped at one instance because the hackathon snapshot repository is process-local.
