# QA fixes deployment — 2026-09-03

The owner explicitly approved deployment after the previous automatic review blocked Cloud Console access. Existing Cloud Shell was reconnected and authorized for the same project. No alternative route was used to bypass the earlier rejection.

## Source and target

- Application source: `94c081c` (QA fixes and regression tests); pushed documentation HEAD before deployment: `f804a69`.
- Fixes: reset drafts on source changes; compare corresponding frame indices after cuts; refuse local caption-removal requests that would otherwise delete footage.
- Existing target: `revisionproof-staging`, project `revisionproof-agentic-2026-kan` / number `348672234012`, region `us-central1`, account `secureis@gmail.com`.
- Preflight verifies the project label, runtime service account, 2 CPU / 4 GiB / concurrency 4, all environment values, and both existing secret references pinned to version 1. Memory write token remains absent. No migrations, billing, credentials or grants changed.
- Source ZIP SHA-256: `226c367ce8309e42b63ff148c51277681860d3c51e5890a61ba7d081a5a39f69`.
- Uploaded bundle SHA-256: `03ba82e98e419f9608518309c42de79483183d6a30ff190f0d83c913f5a58190`; verified again in Cloud Shell before extraction.
- Helper: `.gstack/rp-release-94c081c.sh`, Cloud Shell state `/home/secureis/revisionproof-release-94c081c`, source `/home/secureis/revisionproof-build-94c081c`.
- Build: `87ee838a-ded4-4fb0-b8bc-ee8102fed3d3`, created `2026-09-03T14:03:13.672427321Z`.
- Build SUCCESS at `2026-09-03T14:09:04.145759Z`; preflight/build/push/deploy all SUCCESS.
- Revision `revisionproof-staging-00022-swm`, traffic 100%; Ready, ConfigurationsReady and RoutesReady all True.
- Image digest: `sha256:d73f1ce9e48992e9db98694bde1dd8bc6469219680708d30e2bf304bca722ad9`.
- Browser loaded `index-D7HyN1WC.js`, matching the locally tested frontend. Health, readiness and runtime API return 200; LIVE mutable/ready, 24 MiB and 4–60s limits, intelligence enabled, memory read-only. Credentials configured is readiness only; actual integration execution is checked below.

## Validation

Prior exact-source gates: backend 330 passed / 124.10s; frontend 22 passed; Ruff, ESLint, TypeScript and production build passed. See [the gstack QA report](qa-review-2026-09-03-basic-editor.md).

Deployment succeeded. Only synthetic media is uploaded; the actual KANAPP source remains local. Final delivery approval is not submitted.

- Cut regression LIVE run `01M1KSREVAKEE0D7E71BGQBHV4`: 4s alternating-frame synthetic, actual Gemini draft for cut 0.1–0.2s, one full preview, A export **READY / 3 PASS**, official `mcp-clickhouse.run_query` Change Map with zero review flags; delivery approval false. The same case falsely blocked before the fix. Evidence: `.gstack/qa-release-94c081c/cut-run.json` and `cut-ready.png`.
- Stale-draft LIVE check: prepare a draft using the 10s synthetic video, switch to the 30s sample and re-enter the same request. The old draft remains absent; a new source requires a fresh draft.
- Compound LIVE run `01M1KSXKTCYB5NTBB2MJC5ZQ28`: Korean top subtitle 0–3s, center zoom and English lower text 4–10s, cut 0.5–1s, quiet cut 3.133333–4.866667s explicitly selected after analysis. Actual Gemini draft preserved the literal words; A/B generated; B **READY / 3 PASS**, 10s -> 7.766667s. Official MCP Change Map: 8 windows / 16 samples / zero review flags. Delivery approval false.
- Download: 2,692,936 bytes; downloaded MP4 and selected preview both SHA-256 `e16ae9f9e3bc539f8b9a757174b5371c66480274567ab1db7a5eb40e381a28a3`. Korean and English frames were decoded and inspected. Evidence: `.gstack/qa-release-94c081c/{compound-run.json,summary.json,preview-b.mp4,downloaded.mp4,korean-frame.png,english-frame.png,compound-ready.png}`.
- Both tested flows completed without new browser console errors or HTTP resource failures. Source switches clear the prior draft; comparison at revised 3s maps to original 5.233333s.

## Result

Deployment and gstack LIVE checks are complete. Open [the current editor](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=94c081c); refresh an older tab to load the new bundle. The previous 1b2c0ae deployment and QA rejection records are historical. The low-priority generic Gemini warning noted by QA remains a copy improvement, not a blocking defect. No final human delivery approval was submitted.
