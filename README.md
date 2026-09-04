# RevisionProof

RevisionProof turns video edit requests into reviewable previews and verified exports. Choose basic edits directly or use an editable natural-language draft, approve the exact result, then check it before delivery.

1. Upload MP4/MOV/WebM, up to 24 MiB and 4–60 seconds, or use the sample.
2. Combine center zoom, text, timed subtitle cues, interval cuts and reviewed silence removal. Examples and editable cards show exactly what can run.
3. Review original-video times and exact words. Quiet pauses become optional cut suggestions; the user selects them.
4. Watch full A/B previews (zoom strength/text size). Cut-only plans produce one preview.
5. Choosing a preview freezes spec 3.1 and its SHA-256. The export is an exact copy; media checks and the LIVE ClickHouse MCP feature diff verify the result.
6. Watch the result, use `Adjust edits` if needed, then explicitly approve delivery.

See the [basic editing guide and release evidence](docs/basic-editing-guide-2026-09-03.md) for Korean/English examples, current deployment status and limitations. The original scene-search punch-in proof remains an alternate demo, and its existing spec 2.x JSON/hash contracts remain supported.

## Revision intelligence

With `REVISIONPROOF_INTELLIGENCE_ENABLED=true`, the full-video result includes a sampled **Revision Change Map**. Select a one-second window to compare synchronized, enlarged original/revised players. The map uses two samples per second, not an every-frame guarantee; it does not replace the frozen verification checks.

**Past approved edits** is a collapsed, optional reference area. It searches only when opened, so it does not delay the main review flow. It finds similar, previously verified and human-approved edits; suggestions never auto-select an option. An empty library explains why nothing is available and hides search-engine controls. LIVE retrieval uses the official ClickHouse MCP and supports exact, verified HNSW, and QBit search. Small libraries explicitly use exact search; an empty library reports that no vector engine ran. The public deployment is read-only unless an owner configures a private save key. Local FIXTURE memory is process-local and labelled accordingly.

All edit times refer to the original video; comparisons map around cuts and speed changes. The guided editor supports zoom, literal text, timed subtitles, exact cuts, reviewed quiet-pause removal, 0.5–2× speed, −60 to +12 dB volume, and a bounded uploaded logo. LIVE Gemini can draft editable subtitle cues from Korean, English, or mixed speech without translation. Natural-language edit drafts use Google ADK/Gemini in LIVE and conservative rules locally; direct controls report user-entered plans. Removing text already burned into the original, object/background manipulation, and generated scenes remain outside this build. The existing approved-edit library stores only legacy zoom proofs; multi-edit plans do not show unsupported memory controls. See the [advanced editing guide](docs/advanced-editing-guide-2026-09-04.md).

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

The billed GCP demo is available at [RevisionProof LIVE](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=94c081c). Revision `revisionproof-staging-00022-swm` serves QA-fixed source `94c081c`: source changes clear old drafts, correct cuts no longer falsely BLOCK on adjacent-frame comparisons, and local caption-removal requests cannot suggest footage deletion. Fresh LIVE cut regression and compound run `01M1KSXKTCYB5NTBB2MJC5ZQ28` both reached `READY` with three PASS checks. The compound B video combines Korean subtitles, zoom, English text, a timed cut and selected silence removal; 10 seconds became 7.766667 seconds, with an official MCP map of 8 windows / 16 samples / zero review flags. Download matched the approved preview exactly; text frames and mapped playback were inspected. LIVE QA used synthetic media and final delivery approval remains false. See [latest deployment evidence](docs/deployment-2026-09-03-qa-fixes.md) and the [usage guide](docs/basic-editing-guide-2026-09-03.md). Refresh previously opened tabs. Earlier release and human-approved runs remain separate historical evidence.

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
