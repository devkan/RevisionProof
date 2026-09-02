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

The generated 30-second sample is deliberately visual rather than a blank test pattern:

- 00:00–00:08: editor feedback and agent interpretation
- 00:08–00:14: centered presenter/product reveal used for the A/B punch-in
- 00:14–00:24: source, 1.05x, and 1.12x comparison cards
- 00:24–00:30: verified-delivery card with the locked bottom-right CTA

At the preview step, pause both options near 00:03 to compare crop strength. After choosing B, the app applies that 1.12x punch-in to the full 30-second source, verifies it, and exposes the complete MP4 without asking the operator to upload a revised file.

The deployed LIVE demo is `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. Before a recorded run, confirm `/health` reports `mode=LIVE`, `/ready` reports `status=ready` and `live_credentials_configured=true`, and `/api/runtime` reports `live_ready=true`. `integration_execution_verified=false` at readiness is expected because proof is established per run.

## 90-second judge path

1. Point out the `LIVE` badge and the runtime truth panel.
2. Submit the prefilled three-note brief. Its first note requests a 6-second center `PUNCH_IN`, inside the 4-8 second safety window.
3. Show the checklist: one request is ready, one needs details, and one needs an editor. Select only the ready request; the other two remain unchanged.
4. Point to the `mcp-clickhouse.run_query` scene match, create A/B previews, and open each preview larger near 00:03 to compare crop strength.
5. Choose B (1.12x). Keep the processing banner visible while RevisionProof freezes the spec, builds the complete video, and runs all three checks.
6. Play the final 30-second result in the page or enlarged viewer. Show all three PASS checks and download the generated MP4 if needed.
7. Before the separate delivery action, open raw run JSON and show `state=READY`, the live source labels, `generated_version_url`, and `delivery_approved=false`.
8. Execute **Approve for delivery** only when the demo operator explicitly makes that final decision, then show `delivery_approved=true` and the new human approval event.

The collapsed **Verify a video edited somewhere else** panel is optional. Use it only for an externally produced MP4. The accepted boundary is H.264/AAC MP4, 1280×720, up to 60 seconds, and up to 24 MiB.

## Three-run rehearsal

```powershell
backend/.venv/Scripts/python.exe scripts/rehearse_demo.py --runs 3
```

Only treat the demo as ready when all three runs report `PASS`. Run this again after changing video filters, OpenCV thresholds, state transitions, or container dependencies.

## Live-mode rule

Do not switch the badge to `LIVE` for a recording unless `/ready` is healthy and the run trace itself reports `google.vertex.gemini` plus `mcp-clickhouse.run_query`. Fixture evidence is deterministic development evidence, not a live integration claim. Recorded offline rehearsal mode is read-only.
