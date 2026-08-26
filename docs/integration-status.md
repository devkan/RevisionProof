# Integration status

Updated: 2026-08-26

| Integration | Code path | Local verification | Credential verification |
|---|---|---:|---:|
| FFmpeg / FFprobe | fixed-array commands, timeout, cleanup | PASS | n/a |
| OpenCV checks | punch-in and CTA frame evidence | PASS | n/a |
| Fixture interpreter/index | explicit fixture source labels | PASS | n/a |
| Google ADK + Vertex Gemini | structured interpretation only | package/API contract and mocked service path PASS | PASS; final run source `google.vertex.gemini` |
| Vertex text embedding | `text-embedding-005`, exactly 768 dimensions | contract and client-close test PASS | Vertex endpoint PASS in `global`, 768 dimensions |
| ClickHouse direct writer | append audit facts/spec/checks | adapter INSERT + writer-only role PASS | PASS; final run has 1 spec, 24 features, 6 checks |
| official `mcp-clickhouse` reader | evidence search and version feature diff | real `run_query` + view-only role PASS | PASS; evidence and verification diff both exercised |
| Google Cloud Storage | private media and build-source boundary | local contract PASS | PASS; final v2/v3 objects are private and persisted under the final run |
| Cloud Run | single-container contract and health routes | final non-root image PASS | LIVE PASS; revision `revisionproof-staging-00009-mbh`, concurrency 4, min/max 1 |

The deployed LIVE build is `d5845e1e-9123-4e81-81cb-0fb3f6b607ec` from commit `d1b9a10`; its pushed image digest is `sha256:54e2427d56e8408dfd712c4864df8dec555d127f4b1380a070bbfe2b662e73e3`. Final run `01M0Z3338TYVHWHK4FZRGADTKZ` is the credential-backed evidence. `/ready` keeps `integration_execution_verified=false` because verification is per run, not a process-wide promise.
