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
| Google Cloud Storage | private media and build-source boundary | local contract PASS | PASS; final v2/v3 objects are private and persisted under the final run |
| Cloud Run | single-container contract and health routes | final non-root image PASS | LIVE PASS; revision `revisionproof-staging-00010-k4g`, concurrency 4, min/max 1 |

The deployed LIVE build is `3ebc367e-31a4-4087-abba-6c245cb8c9bc` from commit `4852259`; its pushed image digest is `sha256:c7cd7fc4f9ebc19cbfbc37294fd42d8a79b3e1f9007715f9020a5911b8975cc5`. Recovery run `01M1GN7EY252SSM5F2AM170TKY` is the latest interpreter/MCP evidence; final run `01M0Z3338TYVHWHK4FZRGADTKZ` remains the full delivery proof. `/ready` keeps `integration_execution_verified=false` because verification is per run, not a process-wide promise.
