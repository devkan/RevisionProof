# RevisionProof

> **Deterministic Automated Video Verification & Review Workspace**<br>
> Turn video edit requests into reviewable previews and verified exports. Check approved edits and preserve locked content before delivery.

[![GitHub](https://img.shields.io/badge/GitHub-devkan%2FRevisionProof-181717?logo=github)](https://github.com/devkan/RevisionProof)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Studio%20on%20Cloud%20Run-4285F4?logo=google-cloud)](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo%20(3:14)-FF0000?logo=youtube)](https://youtu.be/KS1vJDMnnW4)

- **Live Studio Demo**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) (Classic UI: [`/`](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/))
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)
- **Source Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)

---

## What is RevisionProof?

A client, editor, or producer can approve one specific video revision without approving unintended side-effects that break locked elements alongside it. RevisionProof solves this with a clear dual guarantee:
1. **Did the requested revision actually happen?**
2. **Did anything previously locked, protected, or balanced regress?**

By maintaining a strict boundary between **AI-assisted drafting** (Google Gemini via Vertex AI and Google ADK) and **deterministic automated verification** (deterministic Python, OpenCV, and FFmpeg), AI never grades its own homework. Only mathematical thresholds and human-in-the-loop sign-off authorize final delivery.

### Studio 6-Step Workflow

**Use sample video** loads the exact KANAPP clip shown in the walkthrough, with no upload required. The [bundled sample record](assets/demo/README.md) includes its checksum and packaging details. The original scene-search proof demo keeps its separate Product Reveal source and scene index.

1. **01 · UPLOAD / SOURCE**: Upload MP4, MOV, or WebM footage (up to 32 MB and 4–60 seconds), or select the pre-loaded 30-second English promo asset (`kanapp_promo_english_editable_30s.mp4`).
2. **02 · EDITS & AI DRAFT**: Combine center punch-in zoom, text overlays, timed or speech-transcribed subtitles (Korean, English, or mixed speech), exact interval cuts, reviewed silence removal, speed adjustments (0.5–2×), volume adjustments (−60 to +12 dB), and a bounded logo overlay. You can write natural-language briefs into structured, editable revision items with Gemini.
3. **03 · CHECK PLAN**: Review original-video timecodes and exact parameters. Incompatible or overlapping edits are flagged before preview rendering.
4. **04 · COMPARE A/B**: Generate and watch competing preview options (e.g., subtle vs. punchy zoom, alternate caption styling) and select the approved candidate. This freezes the specification and its SHA-256 hash (Spec 3.1).
5. **05 · CHECK & VERIFY**: Build the full video or upload an external edited file for audit. Automated checks evaluate:
   - **Approved edit verification** (verifying visual change occurred at the planned timecodes)
   - **Protected content invariants** (ensuring designated CTA or protected regions remain untouched)
   - **Audio invariant limits** (preventing clipping and unexpected volume spikes)
   - **Revision Change Map**: Sampled frame-pair diagnostics (2 samples/second) highlighting requested, unchanged, and review-needed seconds, complete with a synchronized, side-by-side comparative video player for both internal builds and external uploads.
6. **06 · APPROVE & DELIVER**: Human-in-the-loop gate. Only explicit human approval unlocks delivery download and audit logging.

See the [advanced editing guide](docs/advanced-editing-guide-2026-09-04.md) and [basic editing guide](docs/basic-editing-guide-2026-09-03.md) for detailed examples and current controls.

---

## Revision Intelligence & ClickHouse MCP

With intelligence enabled (`REVISIONPROOF_INTELLIGENCE_ENABLED=true`):
- **Revision Change Map**: Samples original and revised video at two frame pairs per second, calculating visual deltas, residual difference from expected edits, and audio decibel changes. Clicking any window displays exact metrics and opens a synchronized side-by-side comparison player.
- **Past Approved Edits Memory**: Powered by the official ClickHouse MCP server (`mcp-clickhouse`). Retrieves similar, previously verified and human-approved edits to provide context and suggested recipes using exact, HNSW, or QBit vector search without delaying the primary editing flow. The public deployment operates in read-only mode to safeguard reference data.

ClickHouse 26.2+ is supported. See the [intelligence runbook](docs/clickhouse-intelligence-runbook.md) for setup, schema, private saving, backup, and restore.

---

## Deployed LIVE Demo

The live Google Cloud Run service is available at:
- **Studio Interface**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- **Classic UI**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/)

**Current Deployment Specifications**:
- **Cloud Run Revision**: `revisionproof-staging-00031-5bl` (Region: `us-central1`)
- **Deployed Application Source**: `b13d8b0` (merged PR #2 containing all caption wrapping, external comparison, and Change Map state fixes)
- **Container Image**: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:44079831-b9b3-4f90-9f01-dee3deb3ac46`
- **Verification Status**: Live health/readiness endpoints (`/health`, `/ready`) return HTTP 200 / LIVE. All 353 backend tests and 78 frontend tests pass with 100% success rate.
- See [Antigravity QA Fixes Deployment Record](docs/deployment-2026-09-07-antigravity-fixes.md) for full deployment logs and live verification evidence.

---

## Local Quick Start

Prerequisites: Python 3.12, Node 22+, uv, FFmpeg/FFprobe, and Noto Sans CJK (Linux) or Malgun Gothic / Arial (Windows) for text rendering. Docker installs the font automatically.

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev --cache-dir backend/.uv-cache
npm install --prefix frontend
backend/.venv/Scripts/python.exe scripts/generate_demo_assets.py
npm run build --prefix frontend
backend/.venv/Scripts/uvicorn.exe revisionproof.main:app --app-dir backend/src --reload --port 8000
```

Open `http://127.0.0.1:8000/studio` for the 6-step Studio workspace, or `http://127.0.0.1:8000` for the classic UI. Fixture mode is labeled in both screens and never emits fake MCP or Gemini calls. `OFFLINE_REHEARSAL` is read-only. `LIVE` mode verifies Google Cloud, GCS, and ClickHouse credentials before reporting readiness.

---

## Quality Gates

```powershell
backend/.venv/Scripts/pytest.exe backend
backend/.venv/Scripts/ruff.exe check backend scripts
backend/.venv/Scripts/ruff.exe format --check backend scripts
npm run lint --prefix frontend
npm run test --prefix frontend
npm run build --prefix frontend
backend/.venv/Scripts/python.exe scripts/rehearse_demo.py --runs 3
docker build --tag revisionproof:local .
backend/.venv/Scripts/python.exe scripts/verify_local_clickhouse.py
backend/.venv/Scripts/python.exe scripts/verify_local_mcp.py
```

---

## Documentation & References

- [Project Handoff & Operation Notes](HANDOFF.md)
- [Documentation Index](docs/README.md)
- [Submission Pack & Release Gates](docs/submission-pack-2026-08-27.md)
- [Antigravity QA Fixes Deployment Record](docs/deployment-2026-09-07-antigravity-fixes.md)
- [ClickHouse Intelligence Runbook](docs/clickhouse-intelligence-runbook.md)
- [Architecture and Trust Boundaries](docs/architecture.md)
- [Security and Failure Policy](docs/security.md)

---

## License

RevisionProof is licensed under the [Apache License, Version 2.0](LICENSE).
