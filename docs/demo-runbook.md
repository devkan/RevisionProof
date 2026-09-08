# Demo runbook

Reviewed: 2026-09-08. This is the English walkthrough for the current Studio. The optional legacy demo is described separately below.

## Start with the KANAPP sample

Open the [live Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) and select **Use sample video**, then **Continue to edits**. It loads `kanapp_promo_english_editable_30s.mp4`, the 30-second English promo used as input in the [product walkthrough](https://youtu.be/KS1vJDMnnW4). You do not need to upload it. The walkthrough itself is 3:14 and is not the sample file.

Try this short review flow:

1. Select **Zoom** and set the edit from **4 to 8 seconds**. You can use the manual controls without waiting for an AI draft.
2. Check the plan and confirm the source time range. Create previews and compare A and B. Watch the result before choosing a version.
3. Choose the preview you want, then select **Build & check full video**. This freezes the plan and checks the generated file against the chosen preview.
4. Read all three checks: export identity, kept scenes on the approved timeline, and approved audio levels. Open a Change Map window to compare the source and result at corresponding moments.
5. Stop at the result if you are only evaluating the workflow. Passing checks do not grant final delivery approval. **Approve for Delivery** is a separate decision for the person reviewing the video.

For a richer edit, add an ending caption or logo, generate editable subtitles from speech, or select a quiet-pause cut. Review each proposed change before rendering. The [editing guide](advanced-editing-guide-2026-09-04.md) lists the supported controls and limits.

## What to look for in the recorded walkthrough

- **Draft, then review:** scene search and Gemini produce a starting point. The presenter adjusts the wording and logo, and corrects a brand name in the subtitle draft.
- **Choose what changes:** speed and volume are adjusted, but only one proposed quiet-pause cut is selected. The rest are left alone.
- **Explain a conflict:** a caption inside a removed interval is flagged. Moving it to the ending resolves the plan conflict.
- **Show a real failure:** a different external file is deliberately submitted and fails the checks. The reviewer can inspect the failed result.
- **Check the replacement:** the selected B version is generated again and passes. This is a new checked result, not automatic repair of the rejected file. Final delivery approval remains pending at the end of the recording.

The [official rules](https://agentic-cinema.devpost.com/rules), checked September 8, evaluate only the first three minutes of a longer video. The current 3:14 cut exceeds that evaluation window; the owner should review what is visible before 3:00. See the [submission checklist](submission-pack-2026-08-27.md) for this and repository-access actions.

## Read the result accurately

- Studio plans require the exported file to match the approved preview byte for byte. An external MP4 is checkable, but a similar-looking re-encode will not pass this identity requirement.
- Visual timeline and audio checks use the frozen criteria. They do not establish that every word, creative choice, or broadcast standard is correct.
- Change Map samples two frame pairs per second. It helps locate moments for review; it is not a full semantic inspection.
- `LIVE` readiness means integrations are configured. Use the run trace to establish actual `google.vertex.gemini` and `mcp-clickhouse.run_query` execution. A manual edit does not prove an AI draft was requested.
- The public approved-edit library is read-only. Empty results are a valid state and do not demonstrate vector search execution.
- Use the bundled sample or non-confidential footage. This public hackathon service has no tenant login, serializes media work, and does not recover in-progress runs after a process restart. A busy service can return HTTP 429; retry after the current job finishes.

## Optional original scene-search demo

The classic UI retains a separate legacy scene-search proof using the generated **Product Reveal** clip. Select the original scene-search demo explicitly. Its scene index and legacy punch-in contract do not belong to the KANAPP sample.

## One-time setup

```powershell
Copy-Item .env.example .env
uv sync --project backend --frozen --extra dev --cache-dir backend/.uv-cache
npm ci --prefix frontend
backend/.venv/Scripts/python.exe scripts/generate_demo_assets.py
npm run build --prefix frontend
```

## Start

```powershell
backend/.venv/Scripts/uvicorn.exe revisionproof.main:app --app-dir backend/src --port 8000
```

Open `http://127.0.0.1:8000/studio` for the current workspace, or `http://127.0.0.1:8000` and select the original scene-search demo for the legacy steps below. This setup uses labeled FIXTURE mode unless you separately configure LIVE dependencies and credentials.

The legacy Product Reveal clip is generated separately from the bundled KANAPP sample:

- 00:00–00:08: editor feedback and agent interpretation
- 00:08–00:14: centered presenter/product reveal used for the A/B punch-in
- 00:14–00:24: source, 1.05x, and 1.12x comparison cards
- 00:24–00:30: verified-delivery card with the locked bottom-right CTA

At the preview step, pause both options near 00:03 to compare crop strength. After choosing B, the app applies that 1.12x punch-in to the full 30-second source, verifies it, and exposes the complete MP4 without asking the operator to upload a revised file.

The deployed LIVE demo is `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. Before a recorded run, confirm `/health` reports `mode=LIVE`, `/ready` reports `status=ready` and `live_credentials_configured=true`, and `/api/runtime` reports `live_ready=true`. `integration_execution_verified=false` at readiness is expected because proof is established per run.

## Legacy scene-search review path

1. Point out the `LIVE` badge and the runtime truth panel.
2. Submit the prefilled three-note brief. Its first note requests a 6-second center `PUNCH_IN`, inside the 4-8 second safety window.
3. Show the checklist: one request is ready, one needs details, and one needs an editor. Select only the ready request; the other two remain unchanged.
4. Point to the `mcp-clickhouse.run_query` scene match, create A/B previews, and open each preview larger near 00:03 to compare crop strength.
5. Choose B (1.12x). Keep the processing banner visible while RevisionProof freezes the spec, builds the complete video, and runs all three checks.
6. Play the final 30-second result in the page or enlarged viewer and inspect the checks. Final delivery remains a separate human decision.
7. Before the separate delivery action, open raw run JSON and show `state=READY`, the live source labels, `generated_version_url`, and `delivery_approved=false`.
8. Execute **Approve for delivery** only when the demo operator explicitly makes that final decision, then show `delivery_approved=true` and the new human approval event.

The collapsed **Verify a video edited somewhere else** panel is optional. Use it only for an externally produced MP4. The accepted boundary is H.264/AAC MP4, 1280×720, up to 60 seconds, and up to 32 MB (32,000,000 bytes).

## Three-run rehearsal

```powershell
backend/.venv/Scripts/python.exe scripts/rehearse_demo.py --runs 3
```

Only treat the demo as ready when all three runs report `PASS`. Run this again after changing video filters, OpenCV thresholds, state transitions, or container dependencies.

## Live-mode rule for recorded integration claims

The badge reflects runtime mode; never relabel fixture output as LIVE for a recording. Claim a successful live AI/MCP demonstration only when readiness is healthy and that run's trace reports `google.vertex.gemini` plus `mcp-clickhouse.run_query`. Fixture evidence is deterministic development evidence, not a live integration claim. Recorded offline rehearsal mode is read-only.
