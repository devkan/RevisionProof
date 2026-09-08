# RevisionProof

> **Make the edit. Check the result. Keep the final say.**
>
> Turn video feedback into editable plans, compare previews, and check the result before delivery. AI helps with the draft. You decide what gets approved.

[![GitHub](https://img.shields.io/badge/GitHub-devkan%2FRevisionProof-181717?logo=github)](https://github.com/devkan/RevisionProof)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Studio%20on%20Cloud%20Run-4285F4?logo=google-cloud)](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo%20(3:14)-FF0000?logo=youtube)](https://youtu.be/KS1vJDMnnW4)

- **Live Studio Demo**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) (Classic UI: [`/`](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/))
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)
- **Source Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)

---

## What is RevisionProof?

When a video is nearly finished, even a small revision means another round of review. Did the new caption appear where it should? Did the cut remove something important? Does the audio still match the version you approved?

RevisionProof brings editing and verification into one workspace for editors, producers, and anyone reviewing a revised video. Google Gemini helps turn feedback into a draft. You adjust the edits and choose a preview. Python, OpenCV, and FFmpeg check the output against that approved version and its frozen criteria. Final delivery still requires your approval.

**For judges:** start with the [demo walkthrough](docs/demo-runbook.md), then see the [submission description and evidence](docs/submission-pack-2026-08-27.md). The 30-second KANAPP input and the 3:14 product walkthrough are different videos.

### Studio 6-Step Workflow

**Use sample video** loads the exact KANAPP clip shown in the walkthrough, with no upload required. The [bundled sample record](assets/demo/README.md) includes its checksum and packaging details. The original scene-search proof demo keeps its separate Product Reveal source and scene index.

1. **01 · UPLOAD / SOURCE**: Upload MP4, MOV, or WebM footage (up to 32 MB and 4–60 seconds), or select the pre-loaded 30-second English promo asset (`kanapp_promo_english_editable_30s.mp4`).
2. **02 · EDITS & AI DRAFT**: Add zoom, text, subtitles, cuts, speed changes, volume adjustments, or a logo. Enter exact settings yourself, or ask Gemini to draft an editable plan. Speech-generated subtitles remain drafts: review names, wording, and timing. Quiet-pause suggestions stay unselected until you choose them.
3. **03 · CHECK PLAN**: Review original-video timecodes and exact parameters. Incompatible or overlapping edits are flagged before preview rendering.
4. **04 · COMPARE A/B**: Watch the preview options and choose the version you want. This freezes the plan and the chosen full-preview SHA-256, a fingerprint of the approved file. Cut-only plans need just one preview.
5. **05 · CHECK & VERIFY**: Build and check the full video, or submit an external MP4 for comparison. For Studio edit plans, three checks evaluate:

   - **Approved preview match:** the export must be byte-for-byte identical to the chosen preview. An external re-encode does not qualify, even if it looks similar.
   - **Kept scenes:** sampled frames are checked against the approved timeline, accounting for cuts and speed changes.
   - **Approved audio:** RMS and peak levels are compared with the approved preview using the frozen limits. This is not a broadcast loudness certification.

   The separate **Revision Change Map** samples two frame pairs per second to help you inspect requested changes and review-needed windows. Its synchronized player is a review aid, not an every-frame or semantic guarantee.

6. **06 · APPROVE & DELIVER**: Review the checks and the video, then make the final delivery decision. Failed or unavailable required checks block delivery. Audit facts are recorded during verification; final approval adds a separate human decision.

See the [editing guide](docs/advanced-editing-guide-2026-09-04.md) for supported controls and examples. The original scene-search demo uses a separate legacy verification contract; it is not the default Studio workflow.

---

## Revision Intelligence & ClickHouse MCP

With intelligence enabled (`REVISIONPROOF_INTELLIGENCE_ENABLED=true`):

- **Smart scene finder**: Describe a scene, review the returned time ranges, and choose where to edit. Google AI describes sampled frames; the official ClickHouse MCP server retrieves matches. This optional action uses Google AI and ClickHouse credits. You can also enter timecodes manually.
- **Revision Change Map**: Samples original and revised video at two frame pairs per second, calculating visual deltas, residual difference from expected edits, and audio decibel changes. Clicking any window displays exact metrics and opens a synchronized side-by-side comparison player.
- **Past Approved Edits Memory**: Retrieves previously verified, human-approved zooms and multi-edit recipes through `mcp-clickhouse`. A recipe can become an editable draft, never an automatic approval. Searches report the actual engine used, with exact fallback when needed; an empty library does not run a vector search. The public demo is read-only. Saving requires a separately configured private workspace key and all approval gates.

ClickHouse 26.2+ is supported. See the [intelligence runbook](docs/clickhouse-intelligence-runbook.md) for setup, schema, private saving, backup, and restore.

---

## Deployed LIVE Demo

The hosted Google Cloud Run service is available at:

- **Studio Interface**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- **Classic UI**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/)

**Deployment evidence recorded on 2026-09-08**:

- **Cloud Run Revision**: `revisionproof-staging-00032-np7` (Region: `us-central1`)
- **Deployed Application Source**: PR #3 merge `a0c589b` (identical tree to deployed archive `621423b`), adding the KANAPP sample while retaining all previous QA fixes.
- **Container Image**: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:1bc66b0f-a094-4f84-8215-925b518b867b`
- **Verification record**: 357 backend tests and 82 frontend tests passed. The deployed KANAPP sample loaded, played, and generated A/B previews. That sample smoke test stopped before final delivery approval and did not claim a new Gemini or MCP execution.
- See the [KANAPP Sample Deployment Record](docs/deployment-2026-09-08-kanapp-sample.md) for source, CI, checksums, and live verification evidence.

`LIVE` readiness confirms configuration, not successful AI or MCP calls in every run. Check each run's trace for execution evidence. In-progress runs are process-local and are not recovered after a service restart. The public demo has no tenant login; use the bundled sample or non-confidential footage.

---

## Local Quick Start

Prerequisites: Python 3.12, Node 22+, uv, FFmpeg/FFprobe, and Noto Sans CJK (Linux) or Malgun Gothic / Arial (Windows) for text rendering. Docker installs the font automatically.

```powershell
Copy-Item .env.example .env
uv sync --project backend --frozen --extra dev --cache-dir backend/.uv-cache
npm ci --prefix frontend
backend/.venv/Scripts/python.exe scripts/generate_demo_assets.py
npm run build --prefix frontend
backend/.venv/Scripts/uvicorn.exe revisionproof.main:app --app-dir backend/src --reload --port 8000
```

Open `http://127.0.0.1:8000/studio` for Studio, or `http://127.0.0.1:8000` for the classic UI. These PowerShell commands use the explicitly labeled FIXTURE setup in `.env.example`; they do not configure cloud credentials. Install the `live` extra and follow the [cloud runbook](docs/gcp-foundation-runbook.md) for LIVE setup. `OFFLINE_REHEARSAL` is read-only. Fixture output is never evidence of real Gemini or MCP execution.

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

- [Judge Demo Walkthrough](docs/demo-runbook.md)
- [Submission Pack & Release Gates](docs/submission-pack-2026-08-27.md)
- [Architecture and Trust Boundaries](docs/architecture.md)
- [Security and Failure Policy](docs/security.md)
- [Documentation Index](docs/README.md), including dated engineering and video-production records, some in Korean
- [Project Handoff & Operation Notes](HANDOFF.md)
- [ClickHouse Intelligence Runbook](docs/clickhouse-intelligence-runbook.md)

---

## License

RevisionProof is licensed under the [Apache License, Version 2.0](LICENSE).
