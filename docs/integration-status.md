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
| Cloud Run | single-container contract and health routes | final non-root image PASS | LIVE PASS; revision `revisionproof-staging-00012-dnv`, concurrency 4, min/max 1 |

The deployed LIVE build is `a38932bf-80ff-4b89-bdde-1353305a72ca` from commit `81521d3`; its pushed image digest is `sha256:e3779de18b356002910c9983c29459cd31fe8c99c2f89e5b6668030d3c5332a8`. Visual-demo run `01M1GVQRHVVZ1TAQRWJZ1H0ACC` is the latest complete runtime proof: Gemini and the official MCP path ran, A/B previews rendered, and the uploaded candidate reached `READY` with three PASS checks. Historical run `01M0Z3338TYVHWHK4FZRGADTKZ` remains the delivery-approved proof. `/ready` keeps `integration_execution_verified=false` because verification is per run, not a process-wide promise.
