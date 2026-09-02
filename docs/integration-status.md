# Integration status

Updated: 2026-09-02

| Integration | Code path | Local verification | Credential verification |
|---|---|---:|---:|
| FFmpeg / FFprobe | fixed-array commands, timeout, cleanup | PASS | n/a |
| OpenCV checks | punch-in and CTA frame evidence | PASS | n/a |
| Fixture interpreter/index | explicit fixture source labels | PASS | n/a |
| Google ADK + Vertex Gemini | structured interpretation only | package/API contract and mocked service path PASS | PASS; final run source `google.vertex.gemini` |
| Vertex text embedding | `text-embedding-005`, exactly 768 dimensions | contract and client-close test PASS | Vertex endpoint PASS in `global`, 768 dimensions |
| ClickHouse direct writer | append audit facts/spec/checks | adapter INSERT + writer-only role PASS | PASS; final run has 1 spec, 24 features, 6 checks |
| official `mcp-clickhouse` reader | evidence search and version feature diff; bounded fresh-process timeout recovery | real `run_query` + view-only role and 3-attempt regression PASS | PASS; recovery run timed out on attempt 1/3 and then anchored three evidence matches |
| Google Cloud Storage | private media and build-source boundary | local contract PASS | PASS; visual source and uploaded verification candidate are private and persisted |
| Cloud Run | single-container contract and health routes | final non-root image PASS | LIVE PASS; revision `revisionproof-staging-00013-gxn`, concurrency 4, min/max 1 |

The deployed LIVE build is `5624e811-29cf-4c4e-a75c-7d22b91bc905` from commit `42750d2`; its pushed image digest is `sha256:8297e01167bcb3f9eb2fbc63c8ae6baee6eb227e7ca593a4624356058672f8b3`. Viewer QA run `01M1GY19CVZZ7QDPG5DPPVBAG9` is the latest Gemini/MCP/A-B-render evidence; visual-demo run `01M1GVQRHVVZ1TAQRWJZ1H0ACC` remains the latest complete `READY` proof, and historical run `01M0Z3338TYVHWHK4FZRGADTKZ` remains the delivery-approved proof. `/ready` keeps `integration_execution_verified=false` because verification is per run, not a process-wide promise.
