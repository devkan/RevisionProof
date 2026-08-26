# Integration status

Updated: 2026-08-26

| Integration | Code path | Local verification | Credential verification |
|---|---|---:|---:|
| FFmpeg / FFprobe | fixed-array commands, timeout, cleanup | PASS | n/a |
| OpenCV checks | punch-in and CTA frame evidence | PASS | n/a |
| Fixture interpreter/index | explicit fixture source labels | PASS | n/a |
| Google ADK + Vertex Gemini | structured interpretation only | package/API contract and mocked service path PASS | Vertex `gemini-3.5-flash-lite` generation PASS in `global`; full ADK interpretation flow NOT RUN |
| Vertex text embedding | `text-embedding-005`, exactly 768 dimensions | contract and client-close test PASS | Vertex endpoint PASS in `global`, 768 dimensions |
| ClickHouse direct writer | append audit facts/spec/checks | adapter INSERT + writer-only role PASS | NOT RUN |
| official `mcp-clickhouse` reader | evidence search and version feature diff | real `run_query` + view-only role PASS | NOT RUN |
| Google Cloud Storage | private media and build-source boundary | local contract PASS | FOUNDATION PASS; private bucket, IAM, lifecycle, and Cloud Build source verified. LIVE candidate object path NOT RUN |
| Cloud Run | single-container contract and health routes | final non-root image PASS | FOUNDATION DEPLOYED; revision `revisionproof-staging-00003-q56`, `/health`, `/ready`, `/api/runtime`, and full FIXTURE flow PASS |

The deployed foundation uses project `revisionproof-agentic-2026-kan`, Cloud Build `354696e9-0fdc-451c-9e69-cf55184ea63f`, and image digest `sha256:d8b4daad7107428776de4339726ba45fc32f60cee204ddf36a1d443f1cba8dfc`. It remains visibly `FIXTURE`; the later Vertex credential probes do not make that revision LIVE. Local ClickHouse verification used 25.6.13 with separate reader/writer users, an append-only convergence check, and TLS disabled only for localhost. ClickHouse Cloud and persisted target rows are still NOT RUN.
