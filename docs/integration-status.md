# Integration status

Updated: 2026-08-25

| Integration | Code path | Local verification | Credential verification |
|---|---|---:|---:|
| FFmpeg / FFprobe | fixed-array commands, timeout, cleanup | PASS | n/a |
| OpenCV checks | punch-in and CTA frame evidence | PASS | n/a |
| Fixture interpreter/index | explicit fixture source labels | PASS | n/a |
| Google ADK + Vertex Gemini | structured interpretation only | package/API contract verified | NOT RUN |
| Vertex text embedding | `text-embedding-005`, exactly 768 dimensions | contract implemented | NOT RUN |
| ClickHouse direct writer | append audit facts/spec/checks | adapter INSERT + writer-only role PASS | NOT RUN |
| official `mcp-clickhouse` reader | evidence search and version feature diff | real `run_query` + view-only role PASS | NOT RUN |
| Google Cloud Storage | version upload object boundary | contract implemented | NOT RUN |
| Cloud Run | single-container contract and health routes | Docker build + probes/static serving PASS | NOT DEPLOYED |

`NOT RUN` and `NOT DEPLOYED` are deliberate: this repository contains no hackathon cloud credentials. Do not convert those cells to PASS until the trace and persisted records are observed in the target project. Local ClickHouse verification used 25.6.13 with separate reader/writer users and TLS disabled only for localhost.
