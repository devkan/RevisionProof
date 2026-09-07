# KANAPP English promo and RevisionProof demo scenarios

Date: 2026-09-04
Last updated: 2026-09-06 — three audience-facing LIVE demo takes completed.

The September 4 scenarios below are preparation templates, not a transcript of the final recordings. For the actual takes, evidence boundaries, and next recording steps, use [the September 6 recording record](#2026-09-06-recording-record).

## Generated demo assets

- Source video: `runtime/demo/kanapp_english_editable_source_30s.mp4`
- Overlay logo: `runtime/demo/kanapp_demo_logo.png`
- Visual storyboard: `runtime/demo/kanapp_promo_storyboard.png`
- Reproducible generator: `scripts/generate_kanapp_promo.py`
- Upload-ready convenience copies: `../video/kanapp_promo_english_editable_30s.mp4` and `../video/kanapp_demo_logo.png`

The source is a 30-second, 1280×720, 30 fps H.264/AAC MP4 with an English voice track. It is intentionally only 0.83 MB, below RevisionProof's 32 MB limit. The factual positioning follows [the KANAPP website](https://www.kanapp.net/): practical AI-powered SaaS products for repeated health, document, approval, and operating workflows.

The upload-ready MP4 SHA-256 is `ce6270bbd3eac7359d173fa34386b8f00ab1bc83c571e0c9bb27e030003d4d91`. The logo SHA-256 is `3e6bb79d8a15c39cad4bf43ab87862a99d69df53bdf001ac3493a62e5ab1e95d`.

## Original local verification and subsequent LIVE boundary

- `ffprobe`: exactly 30.000 seconds, 1280×720, 30 fps, H.264 video, mono 48 kHz AAC audio, 831,549 bytes.
- Full audio/video decode with FFmpeg `-xerror`: PASS.
- RevisionProof source validation for a 0–5 second selection: PASS.
- Main `silencedetect` interval at −42 dB for at least 0.6 seconds: approximately 15.19–18.45 seconds.
- Opening 0–5 second mean/peak: −20.3/−2.6 dB; deliberately quiet 5–10 second mean/peak: −28.3/−10.0 dB; designed 15.2–18.35 second pause mean/peak: −62.9/−48.7 dB.
- The six-scene storyboard was visually inspected after generation.
- Generation source and this guide are tracked in commit `2186575`. The MP4, logo and storyboard are generated artifacts and remain outside Git.
- At creation on September 4, the generated MP4 had only local validation. This limitation was superseded on September 6: the same source was used in three LIVE audience-facing takes, each reaching full verification PASS and final approval waiting. This is observed application evidence, not an independently inspected recording file or a fresh Cloud deployment audit.

## Source timeline and narration

| Time | Picture | English narration | Demo purpose |
|---|---|---|---|
| 0.0–5.0s | Centered KANAPP opening card | “KANAPP turns real operating problems into practical SaaS products.” | Strong center zoom and opening text target |
| 5.0–10.0s | Health, document and approval cards | “We simplify repeated work across health, documents, and approvals.” | Voice is deliberately quieter for volume adjustment |
| 10.0–16.0s | Medical Check and LeanCOO cards | “Medical Check clarifies health data. LeanCOO streamlines business documents.” | English automatic or manual subtitle target |
| 16.0–18.35s | Human-approval transition | No narration | Deliberate quiet pause for reviewed removal |
| 18.35–20.5s | Human-review decision flow | “People review every important decision.” | Clear semantic scene-search target |
| 20.5–26.0s | Find, build and improve loop | “We build working products first, then improve them with real operating data.” | Speed-change target |
| 26.0–30.0s | KANAPP end card | “KANAPP. AI made practical.” | Closing zoom and website-text target |

The lower part of every shot stays relatively clear so generated captions and manual text remain readable. The main detected quiet interval is approximately 15.2–18.45 seconds; the exact suggestion may vary slightly with the configured silence threshold.

## Recording rule

Start every scenario from the original 30-second source. Do not upload the output of one scenario as the source of the next. RevisionProof edit times refer to the original upload, so independent runs are easier to explain and compare.

Before recording, use `New proof`, upload the source, confirm `30.0s`, choose the edits, review the editable plan, create A/B previews, select B when the stronger treatment is preferred, and finish with full-video verification. Leave final delivery approval for the human operator.

## Scenario 1 — Brand impact

Purpose: show the fastest and most visual transformation with three edits plus smart scene search.

### App actions

1. Upload the 30-second source.
2. Turn **Smart scene finder** on and search: `Find the opening KANAPP title.`
3. Select the opening result around 0–5 seconds.
4. Add **Zoom in** for 0.5–4.5 seconds.
5. Add **Text**: `AI, made practical.` for 0.5–4.5 seconds at Bottom center.
6. Add `kanapp_demo_logo.png` with **Add logo** for the full video at Bottom right.
7. Review the three edits, generate A/B previews, choose B, and verify the full video.

### English presenter script

> “I’ll start with a visual brand pass. Smart scene finder locates the opening title using Google AI and ClickHouse. I’ll add a stronger punch-in, a precise tagline, and the KANAPP logo. RevisionProof turns those choices into an editable plan, gives me A and B, and verifies the complete export after I choose.”

### Best moment to record

Pause the B preview near 2 seconds. It should show the larger KANAPP title, the new tagline, and the logo together. This is the strongest thumbnail or short highlight.

## Scenario 2 — Speech and pacing

Purpose: demonstrate the most product depth with five coordinated functions.

### App actions

1. Start a new proof and upload the original source again.
2. Select **English**, then run **Generate editable subtitles**. Quickly review the generated cues and correct `KANAPP`, `Medical Check`, or `LeanCOO` if transcription varies.
3. Run **Find quiet pauses**. Select only the main pause around 15.2–18.45 seconds.
4. Add **Change speed** at 1.25× for 20.5–26.0 seconds.
5. Add **Adjust volume** at +6 dB for 5.0–10.0 seconds.
6. Add **Text**: `www.kanapp.net` for 26.0–30.0 seconds at Bottom right.
7. Review the combined plan, compare A/B, choose B, and verify the complete result.

### English presenter script

> “Now I’ll improve speech and pacing. RevisionProof drafts English subtitles from the actual audio, but keeps every cue editable. It finds quiet pauses for review instead of deleting them automatically. I’ll remove the main pause, lift the deliberately quiet section, speed up the operating loop, and add the website only to the close. One verified result combines all five decisions.”

### Best moment to record

Show the editable subtitle list briefly, then the quiet-pause suggestions, and finally play from about 14 seconds through the shortened transition and faster operating loop. This scenario best demonstrates functional breadth.

## Scenario 3 — Precision editorial pass

Purpose: show exact manual control and the difference between automatic assistance and direct editing.

### App actions

1. Start a new proof and upload the original source again.
2. Keep **Smart scene finder** off and enter times directly.
3. Add **Cut a section** from 15.2–18.35 seconds.
4. Add a manual timed subtitle from 10.25–12.2 seconds: `Medical Check clarifies health data.`
5. Add a second manual timed subtitle from 12.9–15.2 seconds: `LeanCOO streamlines business documents.`
6. Add **Zoom in** from 26.0–30.0 seconds.
7. Add **Text**: `www.kanapp.net` from 26.0–30.0 seconds at Bottom right.
8. Review the five operations, compare A/B, choose the clearer close, and verify the full video.

### English presenter script

> “For a precision pass, I can work entirely with exact times. I’ll cut the transition, place two subtitles on separate product lines, and rebuild the ending with a focused zoom and website. The plan stays readable before rendering, and the final verification checks that the requested changes happened without breaking locked content.”

### Best moment to record

Play from 10 seconds through the two timed subtitles, then jump to the 26-second close. This clearly shows exact cuts, cue replacement, zoom, and URL placement.

## Recommended final demo cut

Use Scenario 1 for the opening impact, Scenario 2 for the central feature demonstration, and a short excerpt from Scenario 3 to prove exact manual control. If the presentation must use only one complete run, choose Scenario 2 because it shows automatic subtitles, reviewed silence removal, speed, volume, text, A/B review, and deterministic verification in one flow.

Across all three scenarios, the eight editor controls are covered:

- Zoom: Scenarios 1 and 3
- Text: Scenarios 1–3
- Timed subtitles: automatic in Scenario 2, manual in Scenario 3
- Exact cut: Scenario 3
- Quiet-pause removal: Scenario 2
- Speed: Scenario 2
- Volume: Scenario 2
- Logo: Scenario 1

## 2026-09-06 recording record

### Intent and operating boundaries

- The user recorded the Codex in-app browser while the assistant operated the deployed Studio at <https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio>.
- These were audience-facing demo takes for later editing, not narrated QA reports to the owner. The user specifically requested deliberate, fluent actions and time to read important screens. Voiceover will be added later; playback was kept muted when used.
- Three takes were completed after an earlier approach was rejected for being too fast/report-oriented. Do not restart the preparation sequence or repeat completed takes unless requested.
- The user announced recording starts. The assistant did not inspect the recorder, saved video paths, recording completeness, or final edited footage. "Take complete" means the browser demonstration finished, not that a recording file was independently verified.
- All takes stopped at **Waiting for you**. No final **Approve & download**, Approved Edit Memory save, submission, publication, or new deployment occurred during these takes or this handoff.
- Browser actions used the user-requested visible in-app browser. This was direct browser verification rather than a separate headless gstack run. Earlier gstack browse guidance informed the workflow; no new full test suite, canary, or benchmark was run for this documentation update.
- Earlier take-1 details are carried forward from the compacted conversation continuity. Recent take-2/take-3 tool observations remain available; exact run IDs and standalone screenshot artifacts for the three takes were not captured in this handoff. Do not substitute historical QA run IDs.

### Take 1 — Find a scene, build the brand edit, verify

1. Smart scene query: `Find the opening KANAPP title.` Eight segments were indexed. The opening 0–4 second result was third, below two closing-title results; the appropriate opening result was explicitly selected. Do not describe the first-ranked result as correct.
2. Natural-language draft: `Zoom in on this opening scene and add "AI, made practical." at the bottom.` The Gemini draft produced zoom and bottom text for 0–4 seconds.
3. Duplicated the text, exposed an overlap warning, then moved the duplicate to 26–30 seconds with `www.kanapp.net` at bottom left.
4. Uploaded `kanapp_demo_logo.png`, placing it at bottom right for 26–30 seconds. Final plan: four operations. Demonstrated excluding/re-including the logo before rendering.
5. Compared/enlarged A and B. B's 1.12× opening crop clipped the baked-in KANAPP label on the left; A's 1.05× crop was selected for clarity. Do not reuse the earlier template's automatic "choose B" advice.
6. Full video passed all three checks: exact preview match = 1, kept frames 60/60, approved audio RMS/peak deltas = 0. Change Map showed 60 frame pairs, requested edits at 0–4 and 26–30 seconds, and unchanged middle footage.
7. Showed enlarged ending, synchronized source/result comparison, technical proof details, then final approval waiting. Captured browser warning/error logs were empty at the take-1 check.

### Take 2 — English speech captions and pacing

1. Created eight English subtitle cues from the actual source audio. Corrected generated `Conab`/`Conab.` to `KANAPP`/`KANAPP.` and `Lean COO` to `LeanCOO`. Automatic transcription remained an editable draft, not guaranteed brand spelling.
2. Approximate draft cues: 0.38–3.79, 5.16–8.52, 10.37–12.01, 12.59–14.8, 18.49–20.25, 21.41–25.12, 26.24–26.97, and 28.05–29.56 seconds. Plan preparation subsequently aligned boundaries to frames; small displayed changes were expected.
3. Quiet-pause search: 0–30 seconds, minimum pause 1 second, Quiet −40 dB. Five proposed cuts appeared, all initially skipped: 4.3–5.3, 8.93–10.2, 15.3–18.33, 20.3–21.2, and 25.2–26.97 seconds. Watched and selected only **15.3–18.33**; other proposals were not applied.
4. Added speed **1.25× at 20.5–26 seconds** and volume **+6 dB at 5–10 seconds**. Eleven applied edits: eight captions, one selected silence cut, speed, volume. No extra closing-URL operation in the actual take.
5. Rendered both smaller/larger-text candidates, inspected enlarged playback, and selected A. Rendering the compound plan took roughly two minutes; cut waiting footage in post-production instead of claiming instant processing.
6. Full checks passed 3/3: exact file match = 1; kept timeline 51/51 sampled frames; approved audio RMS −20.59 dBFS and peak −1.72 dBFS on both reference and result, deltas = 0. These reference values are the approved audio timeline, not the untouched original.
7. Planned final duration was **25.87 seconds**; encoded media reported **25.9 seconds**. Change Map reported 52 frame pairs, no sampled review flags. The check's 51 samples and map's 52 pairs are separate measurements, not a count to silently normalize.
8. Synchronized comparison showed revised 16 seconds mapping to original 19.03 seconds after the cut; revised 19 seconds mapped to original 22.42 seconds inside the speed-adjusted range. Ended at final approval waiting.

### Take 3 — Explain an invalid plan, block the wrong export, recover

1. Added an exact cut at **15.3–18.3 seconds**. Added bottom text `AI that works. Visit kanapp.net` at **15.5–18 seconds**, deliberately entirely inside the cut.
2. The UI marked both affected edits NEEDS FIX, explained which edit removed the text's footage, disabled Check plan, and offered **Fix edit 2**. Used that shortcut and moved the text to **26–30 seconds**. The warning cleared and Check plan became available.
3. Two-edit plan: three-second cut plus ending text. Rendered A/B, inspected ending text, and chose **B**. Expected output: **27 seconds**.
4. **Check an external edit** with the original 30-second source was rejected before full verification: `Revised video duration must match the approved timeline`. This is an input-validation rejection, not a persisted three-check FAIL result.
5. Prepared a clearly named negative demo asset containing source seconds 0–27, so its length matched while its cut location and ending text did not. Uploaded it through the external-edit control; no API/state injection or fabricated proof was used.
6. This same-duration wrong export produced **BLOCKED, 0/3 checks pass**:
   - `APPROVED_PATCH_MISMATCH`: normalized/exact match 0.
   - `UNEXPECTED_VIDEO_CHANGE`: 53/54 timeline samples passed, below the required ratio of 1.
   - `LOCKED_AUDIO_CHANGED`: peak delta 0.88 dB exceeded 0.1 dB; RMS delta was 0.49 dB.
7. The Change Map highlighted **11 seconds to review**, using 54 frame pairs. Showed failed check cards, the 15–16 and 23–24 second diagnostic windows, and the available repair controls. **Compare this moment was disabled for this external failed result**; no failed-result side-by-side comparison was demonstrated.
8. **Run checks again** built the selected B version through the app and reverified that newly generated result. It did not somehow make the previously uploaded wrong file pass, and no hand-edited corrected external upload was claimed.
9. New result: **PASS, 3/3**, exact file match = 1, kept frames 54/54, approved audio RMS/peak deltas = 0. Map: 54 pairs, no sampled review flags. Showed the 24-second revised ending against original 27 seconds with the requested text, plus preserved 14-second footage and synchronized playback through the cut.
10. Final screen: **Version B · 2 edits · 30s → 27s · PASS · Waiting for you**. A read-only browser check during handoff confirmed this same screen. No final approval or download was clicked.

### Negative demo asset and reproduction

Preserve the original source and logo. The new file is intentionally wrong and must never be used as the next take's source or described as an approved export:

- `D:\Hackathon\006.Agentic Cinema Hackathon\video\take3_wrong-edit_same-duration_27s.mp4`
- Handoff filesystem check: 698,364 bytes. Source remained 831,549 bytes; logo remained 8,509 bytes.
- It is outside the Git repository, alongside the original demo media. No original was overwritten.

Executed generation command (the `-n` option refuses overwriting an existing output):

```powershell
ffmpeg -hide_banner -loglevel error -n -i 'D:\Hackathon\006.Agentic Cinema Hackathon\video\kanapp_promo_english_editable_30s.mp4' -t 27 -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 128k -movflags +faststart 'D:\Hackathon\006.Agentic Cinema Hackathon\video\take3_wrong-edit_same-duration_27s.mp4'
```

This removes the final three seconds, whereas the selected plan removes the middle 15.3–18.3 seconds and adds text. Re-encoding can also change audio measurements; do not attribute every failed metric solely to the cut.

### Extra ClickHouse evidence footage — not yet recorded/verified in console

The core functional demonstration is complete. Editorial recommendation: add 10–15 seconds of technical evidence, not a long console tour. This is presentation advice, not a claim about mandatory competition rules.

1. **ClickHouse Cloud → the existing RevisionProof service → Monitoring → Query insights**. Select a time window including the recordings, find `revision_change_map` SELECT queries in Recent queries, then open **Query history** to show actual executions and processing times. If recent-24-hours no longer includes the recordings, use a custom interval. Do not claim a manual console SELECT is itself proof that the official MCP executed it.
2. **Same service → SQL Console → New Query → Run**. The following read-only query selects checks from the run with the most recent stored check timestamp. It was checked against `infra/clickhouse/schema.sql`, but **was not executed in ClickHouse Cloud during this conversation**:

```sql
SELECT checked_at, version_label, check_id, verdict, failure_code
FROM revisionproof.version_checks
WHERE run_id = (
    SELECT argMax(run_id, checked_at)
    FROM revisionproof.version_checks
)
ORDER BY checked_at, check_id;
```

For the take-3 run, the intended footage is the failed external-result records followed by the regenerated PASS records. If another run is newer, identify the intended `run_id` from authorized read-only records and replace the subquery with that explicit ID. Do not fabricate an ID, insert demonstration rows, or present unrelated historical checks as this recording. Console access must have SELECT permission on `version_checks`; the least-privilege MCP reader is restricted to views and may not read this raw table.

Optional run-ID lookup before filming:

```sql
SELECT run_id, max(checked_at) AS last_check
FROM revisionproof.version_checks
GROUP BY run_id
ORDER BY last_check DESC
LIMIT 10;
```

The app footage already includes **Check → Revision Change Map → How this map was measured**, showing `mcp-clickhouse.run_query`, sample counts, and diagnostics. Combine that with the matching console evidence. GCP can be represented with one accurate Cloud Run/Gemini architecture slide; no new slide or console footage has been produced here. Do not record passwords, connection strings, tokens, billing identifiers, unrelated projects, or sensitive query contents.

Official menu references checked on September 6:

- [Query insights](https://clickhouse.com/docs/products/cloud/features/sql-console-features/query-insights)
- [SQL Console](https://clickhouse.com/docs/products/cloud/features/sql-console-features/sql-console)

### Resume safely and known rough edges

- Keep the current Studio tab intact. Runs are process-local; reload/navigation/restart can lose the workspace. During this conversation it was browser `1`, tab `4`; future sessions must rediscover it rather than trust those IDs.
- In this UI **New review** retained the original source and cleared the edit plan. Tool buttons add operations; templates replace the whole list. Never click a template after generating captions unless replacement is intended.
- Use source-time ranges. Set a later End before a later Start to avoid transient invalid ranges. Setting End to the source duration while Start is zero can toggle full-video mode and hide time fields.
- Native enlarged/final players may start unmuted. Check before playing. Read-only DOM media state and native controls were used; buffering and hidden native controls caused occasional automation retries, not backend failures. Playback can reach the end while a tool call is pending; do not blindly toggle Space or assume Pause both still exists.
- Take 2's long operating-loop subtitle wrapped within a word in the compact side-by-side view. This was not fixed or separately reviewed. If the user requests polish, reproduce after recording, not during a take.
- On take-3 BLOCKED → PASS refresh, the selected Change Map detail temporarily retained its earlier diagnostic text until a different time window was selected. The badges/overall proof had changed to PASS. Record as a follow-up state-refresh issue, not a verified source diagnosis; no code fix or deployment occurred.
- External failed-result Compare this moment was disabled. Its reason was not diagnosed here. Do not claim that path was demonstrated or fixed.
- Optional gstack telemetry was previously rejected by the environment because of external metadata transmission. It was not retried or bypassed; it is not a blocker to recording or local handoff.
- Earlier eligibility discussion raised a development-tool restriction concern. Recording, Gemini runtime use, or deleting provenance does not resolve it. Do not rewrite history, promise eligibility, or submit automatically; fresh official/case-specific confirmation remains separate if requested.

### Remaining work

1. User confirms the three recording files were saved, then selects/edits the strongest segments and adds voiceover. Actual recordings have not been opened or edited by the assistant.
2. If desired, record matching ClickHouse execution/check-history evidence using the read-only paths above; verify results before narration. No console query or filter was executed by the assistant.
3. Keep final delivery approval and any hackathon submission as separate user decisions. There is no pending deployment from the recording task.
4. This handoff edits documentation only. Review/commit/push these docs only when requested; do not redeploy solely for them.
