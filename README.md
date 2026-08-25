# RevisionProof

RevisionProof is a deterministic approval firewall for video revisions. It converts ambiguous client feedback into an evidence-anchored `RevisionSpec`, produces constrained A/B punch-in previews, and blocks publishing when a new version violates the approved patch or a locked creative element.

The hackathon path is deliberately narrow:

1. Index a 720p demo video and classify three notes as auto-previewable, clarification, or manual creative work.
2. Anchor only the safe punch-in note to actual scene evidence; unsupported notes never execute.
3. Generate two constrained 4–8 second punch-in previews (1.05x and 1.12x).
4. Human approval freezes an immutable, SHA-256-addressed spec.
5. Upload v2: the requested patch passes, but a missing CTA blocks publishing.
6. Upload v3: all deterministic checks pass and the human `Approve for Delivery` gate becomes available.

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

## Deployed foundation demo

The billed GCP foundation deployment is available at `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. It is intentionally labeled `FIXTURE` and proves the isolated Cloud Build, Artifact Registry, GCS, IAM, and Cloud Run path. It is not Gemini or ClickHouse LIVE evidence.

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
```

See the [documentation index](docs/README.md), [architecture](docs/architecture.md), [demo runbook](docs/demo-runbook.md), [latest QA report](docs/qa-report-2026-08-26-cloud-deploy.md), [deployment inventory](docs/infrastructure-inventory-2026-08-26.md), and [project handoff](HANDOFF.md).
