# Security and failure policy

- Uploads accept MP4 only, at most 24 MiB and 60 seconds, with H.264 video, AAC audio, and 1280x720 dimensions.
- Idempotent version uploads require a 64-character SHA-256 header, verify it against the received stream, and reject missing or mismatched digests before processing.
- Media commands are argument arrays, never shell-composed strings. A non-blocking pipeline lock permits one render/verification workflow at a time, and timed-out commands remove partial outputs.
- Public media routes allow only bundled demos, A/B previews, and CTA proof PNGs. Uploaded candidate versions and arbitrary runtime paths return 404.
- Run and version identifiers are validated before SQL is built. Embeddings must have exactly 768 numeric values and query limits are bounded.
- The MCP ClickHouse credential receives SELECT only on two views. The writer credential receives INSERT only on `revision_specs`, `version_features`, and `version_checks`; provisioning removes unexpected direct grants and inherited roles before assigning the locked defaults.
- Reader and writer usernames/passwords are separate settings; assign `revisionproof_mcp_reader` and `revisionproof_writer` as their default roles during ClickHouse provisioning.
- Secrets enter Cloud Run through Secret Manager; they are not committed or returned by the API. Deployments pin numeric secret versions instead of `latest`, and secret IAM refuses any accessor other than the RevisionProof runtime service account.
- GCS runtime access is bucket-scoped `objectCreator` plus `objectViewer`. Candidate objects use generation preconditions and SHA-256 metadata, so the runtime cannot overwrite or delete existing media.
- The Cloud Build service account uses the project-local `revisionproofCloudRunDeployer` custom role instead of `roles/run.admin`. Its permissions are limited to creating/updating/reading Cloud Run services and their public-access policy.
- ClickHouse destructive cleanup requires the exact TLS Cloud host, project ID, database name, explicit `--execute`, and a matching database sentinel.
- A proof allows publishing only when every deterministic check is `PASS`. Empty checks, unavailable checks, exceptions, or integration failures are blocked.
- Revision specs are frozen after approval. A new approval requires a new run and hash.
- Revision spec validation recomputes the canonical hash and binds the approved time range, locked ranges, ROI, and threshold keys.
- `FIXTURE`, `OFFLINE_REHEARSAL`, `LIVE`, and `UNAVAILABLE` are user-visible execution modes; `OFFLINE_REHEARSAL` and `UNAVAILABLE` reject state-changing requests. Fixture-only demo routes reject LIVE requests.
- The container runs as an unprivileged UID. Cloud Run is capped at one instance because the hackathon snapshot repository is process-local.
