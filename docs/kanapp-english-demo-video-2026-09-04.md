# KANAPP English promo and RevisionProof demo scenarios

Date: 2026-09-04

## Generated demo assets

- Source video: `runtime/demo/kanapp_english_editable_source_30s.mp4`
- Overlay logo: `runtime/demo/kanapp_demo_logo.png`
- Visual storyboard: `runtime/demo/kanapp_promo_storyboard.png`
- Reproducible generator: `scripts/generate_kanapp_promo.py`
- Upload-ready convenience copies: `../video/kanapp_promo_english_editable_30s.mp4` and `../video/kanapp_demo_logo.png`

The source is a 30-second, 1280×720, 30 fps H.264/AAC MP4 with an English voice track. It is intentionally only 0.83 MB, below RevisionProof's 32 MB limit. The factual positioning follows [the KANAPP website](https://www.kanapp.net/): practical AI-powered SaaS products for repeated health, document, approval, and operating workflows.

The upload-ready MP4 SHA-256 is `ce6270bbd3eac7359d173fa34386b8f00ab1bc83c571e0c9bb27e030003d4d91`. The logo SHA-256 is `3e6bb79d8a15c39cad4bf43ab87862a99d69df53bdf001ac3493a62e5ab1e95d`.

## Local verification and current boundary

- `ffprobe`: exactly 30.000 seconds, 1280×720, 30 fps, H.264 video, mono 48 kHz AAC audio, 831,549 bytes.
- Full audio/video decode with FFmpeg `-xerror`: PASS.
- RevisionProof source validation for a 0–5 second selection: PASS.
- Main `silencedetect` interval at −42 dB for at least 0.6 seconds: approximately 15.19–18.45 seconds.
- Opening 0–5 second mean/peak: −20.3/−2.6 dB; deliberately quiet 5–10 second mean/peak: −28.3/−10.0 dB; designed 15.2–18.35 second pause mean/peak: −62.9/−48.7 dB.
- The six-scene storyboard was visually inspected after generation.
- Generation source and this guide are tracked in commit `2186575`. The MP4, logo and storyboard are generated artifacts and remain outside Git.
- The generated MP4 has not yet been uploaded to LIVE or taken through a complete RevisionProof A/B and verification run. Do not report a LIVE result until that rehearsal is observed.

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
