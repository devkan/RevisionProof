# Automatic full-video workflow and UI QA — 2026-09-02

Result: **PASS**. RevisionProof now separates client requests into executable, clarification-required, and editor-required work; lets the user select only a safe request; renders A/B previews; applies the chosen option to the complete source video; and verifies the generated MP4 without requiring the user to manufacture and upload a revised file.

## Product and UI changes

- Client notes are rendered as readable request cards with real checkboxes. Unsupported or ambiguous requests are visibly held back instead of being silently ignored.
- The workflow is a four-step rail: source and notes, request review, A/B comparison, then full-video build and verification.
- Source, A, B, and final videos have viewport-bounded enlarged viewers.
- Long-running Gemini, ClickHouse MCP, FFmpeg, and verification phases expose a sticky processing banner and spinner with phase-specific copy.
- The primary B action is `Choose B and build full video`; the previous external MP4 upload is retained only as a collapsed secondary path for verifying a video edited elsewhere.
- The final delivery approval remains a separate human gate after playback and deterministic checks.

## Automated verification

- Backend: 108 pytest tests PASS.
- Python quality: Ruff check PASS; 46 files pass formatting verification.
- Frontend: five Vitest files / eight tests PASS; ESLint PASS; production build PASS.
- Docker: `revisionproof:local`, image ID `sha256:b113b70008414e545c37694e01be93a3e682ac94c07b153b4938c0d20bea995e`, built successfully.
- gstack local browser QA covered request selection, A/B rendering, automatic full render, final download, spinner visibility, mobile/desktop overflow, and browser console state.
- gstack design review improved the baseline from D to A- and goodwill from 35 to 88. The final rendered UI has no text below 12 px, 44 px interaction targets, and no horizontal overflow at 375 px or 1280 px.
- gstack pre-landing review found four informational issues; all were fixed. Final review score: 9.5/10 with no unresolved findings.

## Guarded LIVE deployment

- Exact account: `secureis@gmail.com`
- Exact project: `revisionproof-agentic-2026-kan` (`348672234012`)
- Source commit: `6012e9f`
- Cloud Build source: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788354791.102835-030f2a34fe4b46b3b95d3dff1a273dbb.tgz`
- Cloud Build: `c0c3c928-fd5a-47a3-9b04-14ec5fbcbc20`, `SUCCESS`
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:c0c3c928-fd5a-47a3-9b04-14ec5fbcbc20`
- Digest: `sha256:d434e6fbe4e5d9e5be2ea47af590aaf4ffec5cc868cce36238db59d64458aef7`
- Cloud Run revision: `revisionproof-staging-00014-r4l`, 100% traffic
- Stable URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- Health: `/health`, `/ready`, and `/api/runtime` PASS in `LIVE` mode.

No other GCP project was selected or modified. This deployment added a build-source object, Cloud Build record, Artifact Registry image version, and Cloud Run revision inside the dedicated RevisionProof project; it introduced no new resource type. Existing guarded inventory and cleanup scripts remain the source of truth for later removal.

## LIVE end-to-end proof

Run `01M1H4MDB7NQBDFQF1YNNFM0EB` completed this path:

1. Vertex Gemini classified the three client notes as one ready request, one request needing details, and one request needing an editor.
2. The checked six-second punch-in request was anchored through `mcp-clickhouse.run_query` to `0:08–0:14`.
3. A/B previews rendered; Option B was selected.
4. The server generated the complete revised MP4 and verified it with OpenCV/FFmpeg plus the ClickHouse MCP feature-diff path.
5. The final 30.016-second, 1280×720 video loaded in the inline player and enlarged dialog. Download is available from `/api/runs/01M1H4MDB7NQBDFQF1YNNFM0EB/generated-video`.
6. All three locked checks passed: approved punch-in, CTA visibility, and audio level.

Private GCS persistence was independently checked with an explicit project flag:

- Object: `gs://revisionproof-agentic-2026-kan-media/runs/01M1H4MDB7NQBDFQF1YNNFM0EB/versions/approved-b.mp4`
- Size: 817,180 bytes
- Generation: `1788355551327949`

The browser console contained no warnings or errors. The final human `Approve for delivery` control was intentionally not pressed during QA.

## Local-only evidence

Detailed screenshots and generated audit reports remain under the ignored `.gstack/design-reports/` and `.gstack/qa-reports/` directories. They are reproducible QA artifacts, not application inputs or deployment resources.
