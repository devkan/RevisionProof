# RevisionProof

RevisionProof turns video edit requests into reviewable previews and verified exports. Choose basic edits directly or use an editable natural-language draft, approve the exact result, then check it before delivery.

1. Upload MP4/MOV/WebM, up to 24 MiB and 4–60 seconds, or use the sample.
2. Combine center zoom, text, timed subtitle cues, interval cuts and reviewed silence removal. Examples and editable cards show exactly what can run.
3. Review original-video times and exact words. Quiet pauses become optional cut suggestions; the user selects them.
4. Watch full A/B previews (zoom strength/text size). Cut-only plans produce one preview.
5. Choosing a preview freezes spec 3.0 and its SHA-256. The export is an exact copy; media checks and the LIVE ClickHouse MCP feature diff verify the result.
6. Watch the result, use `Adjust edits` if needed, then explicitly approve delivery.

See the [basic editing guide and release evidence](docs/basic-editing-guide-2026-09-03.md) for Korean/English examples, current deployment status and limitations. The original scene-search punch-in proof remains an alternate demo, and its existing spec 2.x JSON/hash contracts remain supported.

## Revision intelligence

With `REVISIONPROOF_INTELLIGENCE_ENABLED=true`, the full-video result includes a sampled **Revision Change Map**. Select a one-second window to compare synchronized, enlarged original/revised players. The map uses two samples per second, not an every-frame guarantee; it does not replace the frozen verification checks.

**Past approved edits** is a collapsed, optional reference area. It searches only when opened, so it does not delay the main review flow. It finds similar, previously verified and human-approved edits; suggestions never auto-select an option. An empty library explains why nothing is available and hides search-engine controls. LIVE retrieval uses the official ClickHouse MCP and supports exact, verified HNSW, and QBit search. Small libraries explicitly use exact search; an empty library reports that no vector engine ran. The public deployment is read-only unless an owner configures a private save key. Local FIXTURE memory is process-local and labelled accordingly.

All edit times refer to the original video; comparisons map around removed sections. LIVE natural-language drafts use Google ADK/Gemini, local drafts use conservative rules, and direct controls report user-entered plans. Text is literal overlays, not automatic speech transcription or removal of text already burned into the original. Object/background manipulation and generated scenes are outside this build. The existing approved-edit library stores only legacy zoom proofs; multi-edit plans do not show unsupported memory controls.

ClickHouse 26.2+ is required. Existing installations must run the additive migration before enabling the feature. See the [intelligence runbook](docs/clickhouse-intelligence-runbook.md) for setup, private saving, trial-expiry export, restore, and rollback. The extension is enabled on the LIVE demo; its migration, deployment and persisted evidence are in the [2026-09-03 release record](docs/deployment-2026-09-03-clickhouse-intelligence.md).

## Local quick start

Prerequisites: Python 3.12, Node 22+, uv, FFmpeg/FFprobe, and Noto Sans CJK (Linux) or Malgun Gothic (Windows) for text rendering. Docker installs the font.

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev --cache-dir backend/.uv-cache
npm install --prefix frontend
backend/.venv/Scripts/python.exe scripts/generate_demo_assets.py
npm run build --prefix frontend
backend/.venv/Scripts/uvicorn.exe revisionproof.main:app --app-dir backend/src --reload --port 8000
```

Open `http://127.0.0.1:8000`. Fixture mode is labeled in the UI and never emits a fake MCP or Gemini success. `OFFLINE_REHEARSAL` is read-only. `LIVE` mode fails readiness until Google Cloud, GCS, and ClickHouse settings are present.

## Deployed LIVE demo

The billed GCP demo is available at [RevisionProof LIVE](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=1c12046). Revision `revisionproof-staging-00017-cnr` serves source `1c12046`, including upload audio-baseline and request-recovery fixes. Fresh synthetic LIVE run `01M1K7XV7QF85PVHE9Q1EKD9HQ` used Gemini, selected 4–10 seconds, and generated the complete Option B video. It reached `READY` with three PASS checks and an official MCP-backed Change Map of 10 windows / 20 samples, with no review flags. Unchanged positive decoded audio peaks passed; playback and MP4 download passed. Final delivery approval was not granted. The owner's actual KANAPP file passed local checks; post-deploy LIVE retransmission requires explicit approval. See the [current fix and deployment record](docs/kanapp-demo-fix-2026-09-03.md). Previously opened tabs may need a hard refresh. The [preceding upload release](docs/deployment-2026-09-03-source-upload.md) and historical delivery-approved run `01M0Z3338TYVHWHK4FZRGADTKZ` remain separate evidence.

`/ready` deliberately reports that integrations are configured, not that every future call will succeed. Treat a run as LIVE evidence only when its raw JSON shows successful integration results and the matching ClickHouse evidence. The historical 2026-08-26 run received separate human delivery approval; the new upload QA run remains unapproved for delivery.

## Quality gates

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

See the [documentation index](docs/README.md), [architecture](docs/architecture.md), [demo runbook](docs/demo-runbook.md), [automatic full-video and UI QA](docs/qa-report-2026-09-02-automatic-full-video-ui.md), [full LIVE delivery QA](docs/qa-report-2026-08-26-live-final.md), [deployment inventory](docs/infrastructure-inventory-2026-08-26.md), and [project handoff](HANDOFF.md).
