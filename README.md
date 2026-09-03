# RevisionProof

RevisionProof is a deterministic approval firewall for video revisions. It converts ambiguous client feedback into an evidence-anchored `RevisionSpec`, produces constrained A/B punch-in previews, and blocks publishing when a new version violates the approved patch or a locked creative element.

The hackathon path is deliberately narrow:

1. Upload an original MP4/MOV/WebM (up to 24 MiB, 4–60 seconds), or use the indexed sample. For an upload, choose the 4–8 second section to edit; the app prepares a 720p working copy while preserving aspect ratio.
2. Present the result as a checklist. Only the explicitly selected, evidence-grounded punch-in may execute; the other requests remain unchanged.
3. Generate two constrained 4–8 second punch-in previews (1.05x and 1.12x).
4. Choosing A or B freezes an immutable, SHA-256-addressed spec and applies that option to the complete source, preserving its duration.
5. FFmpeg and OpenCV verify the requested patch, protected video content, and audio levels. Uploaded originals use sampled full-video checks; the bundled sample retains its specific CTA check. A passing result is available to watch and download.
6. A separate human `Approve for delivery` gate remains required. Uploading an externally edited MP4 is available only as a secondary verification path.

## Revision intelligence

With `REVISIONPROOF_INTELLIGENCE_ENABLED=true`, the full-video result includes a sampled **Revision Change Map**. Select a one-second window to compare synchronized, enlarged original/revised players. The map uses two samples per second, not an every-frame guarantee; it does not replace the frozen verification checks.

**Past approved edits** is a collapsed, optional reference area. It searches only when opened, so it does not delay the main review flow. It finds similar, previously verified and human-approved edits; suggestions never auto-select an option. An empty library explains why nothing is available and hides search-engine controls. LIVE retrieval uses the official ClickHouse MCP and supports exact, verified HNSW, and QBit search. Small libraries explicitly use exact search; an empty library reports that no vector engine ran. The public deployment is read-only unless an owner configures a private save key. Local FIXTURE memory is process-local and labelled accordingly.

Uploaded-video timing comes from the user's selection, not automatic transcription or scene recognition. LIVE classifies the feedback with Gemini; FIXTURE uses explicitly labelled local rules. Only center punch-in is automated; text, captions and logos are unsupported. `Edit request` keeps the file, range and wording available for correction. See the [upload and memory UX guide](docs/source-upload-and-memory-ux-2026-09-03.md) for usage, limits, and verification. These upload/UX changes are deployed and verified on the LIVE service below.

ClickHouse 26.2+ is required. Existing installations must run the additive migration before enabling the feature. See the [intelligence runbook](docs/clickhouse-intelligence-runbook.md) for setup, private saving, trial-expiry export, restore, and rollback. The extension is enabled on the LIVE demo; its migration, deployment and persisted evidence are in the [2026-09-03 release record](docs/deployment-2026-09-03-clickhouse-intelligence.md).

## Local quick start

Prerequisites: Python 3.12, Node 22+, uv, and FFmpeg/FFprobe.

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
