# Demo runbook

## One-time setup

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev --cache-dir backend/.uv-cache
npm install --prefix frontend
backend/.venv/Scripts/python.exe scripts/generate_demo_assets.py
npm run build --prefix frontend
```

## Start

```powershell
backend/.venv/Scripts/uvicorn.exe revisionproof.main:app --app-dir backend/src --port 8000
```

Open `http://127.0.0.1:8000`.

## 90-second judge path

1. Point out the `FIXTURE MODE` badge and the runtime truth panel.
2. Submit: `Can we make the product reveal feel more intentional?`
3. Show the three time-coded evidence matches and their source.
4. Render A/B and approve B (1.12x).
5. Point to the frozen SHA-256 spec hash.
6. Select **Verify demo v2**. The approved patch and audio pass, the hidden CTA regression fails, and the release gate reads `PUBLISH BLOCKED`.
7. Select **Verify repaired v3**. All checks pass and the release gate reads `PUBLISH READY`.
8. Open raw run JSON from the proof trace if a judge asks for machine-readable evidence.

## Three-run rehearsal

```powershell
backend/.venv/Scripts/python.exe scripts/rehearse_demo.py --runs 3
```

Only treat the demo as ready when all three runs report `PASS`. Run this again after changing video filters, OpenCV thresholds, state transitions, or container dependencies.

## Live-mode rule

Do not switch the badge to `LIVE` for a recording unless `/readyz` is healthy and the run trace itself reports `google.vertex.gemini` plus `mcp-clickhouse.run_query`. Fixture evidence is valid for offline rehearsal only.
