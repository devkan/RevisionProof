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

The deployed LIVE demo is `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. Before a recorded run, confirm `/health` reports `mode=LIVE`, `/ready` reports `status=ready` and `live_credentials_configured=true`, and `/api/runtime` reports `live_ready=true`. `integration_execution_verified=false` at readiness is expected because proof is established per run.

## 90-second judge path

1. Point out the `LIVE MODE` badge and the runtime truth panel.
2. Submit the prefilled three-note brief. Show `AUTO PREVIEW`, `CLARIFY`, and `MANUAL`; only the first may execute.
3. Show the three time-coded evidence matches and the `mcp-clickhouse.run_query` source.
4. Render A/B and approve B (1.12x), matching the final verified run.
5. Point to the frozen SHA-256 spec hash.
6. Upload `runtime/demo/revisionproof_v2_blocked.mp4`. The approved patch and audio pass, the hidden CTA regression fails, before/after frames appear, and both the release gate and delivery button are blocked.
7. Upload `runtime/demo/revisionproof_v3_ready.mp4`. All checks pass and the release gate reads `PUBLISH READY`.
8. Before the separate delivery action, open raw run JSON and show `state=READY`, the live source labels, and `delivery_approved=false`.
9. Execute **Approve for Delivery** only when the demo operator has explicitly chosen to make that final delivery decision, then show `delivery_approved=true` and the new human approval event. Final evidence run `01M0Z3338TYVHWHK4FZRGADTKZ` has completed this step.

## Three-run rehearsal

```powershell
backend/.venv/Scripts/python.exe scripts/rehearse_demo.py --runs 3
```

Only treat the demo as ready when all three runs report `PASS`. Run this again after changing video filters, OpenCV thresholds, state transitions, or container dependencies.

## Live-mode rule

Do not switch the badge to `LIVE` for a recording unless `/ready` is healthy and the run trace itself reports `google.vertex.gemini` plus `mcp-clickhouse.run_query`. Fixture evidence is deterministic development evidence, not a live integration claim. Recorded offline rehearsal mode is read-only.
