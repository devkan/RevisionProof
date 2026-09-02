# RevisionProof

RevisionProof is a deterministic approval firewall for video revisions. It converts ambiguous client feedback into an evidence-anchored `RevisionSpec`, produces constrained A/B punch-in previews, and blocks publishing when a new version violates the approved patch or a locked creative element.

The hackathon path is deliberately narrow:

1. Index a 720p demo video and classify every client request as ready to automate, needing details, or needing an editor.
2. Present the result as a checklist. Only the explicitly selected, evidence-grounded punch-in may execute; the other requests remain unchanged.
3. Generate two constrained 4–8 second punch-in previews (1.05x and 1.12x).
4. Choosing A or B freezes an immutable, SHA-256-addressed spec and applies that option to the full 30-second source.
5. FFmpeg and OpenCV automatically verify the requested patch, locked CTA, and audio continuity. A passing result is available to watch and download.
6. A separate human `Approve for delivery` gate remains required. Uploading an externally edited MP4 is available only as a secondary verification path.

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

The billed GCP demo is available at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. The exact current revision, build, image digest, and verification run are recorded in the dated deployment inventory and QA reports. Automatic-render run `01M1H4MDB7NQBDFQF1YNNFM0EB` used `google.vertex.gemini` and `mcp-clickhouse.run_query`, generated the selected Option B across the complete source, and reached `READY` with three PASS checks. Historical delivery-approved run `01M0Z3338TYVHWHK4FZRGADTKZ` remains evidence for the earlier external-upload path.

`/ready` deliberately reports that integrations are configured, not that every future call will succeed. Treat a run as LIVE evidence only when its raw JSON shows the live source labels and the matching ClickHouse rows exist. The verified final run is `READY` and received its separate human delivery approval (`delivery_approved=true`) on 2026-08-26.

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
