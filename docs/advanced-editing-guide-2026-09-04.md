# Editing guide

User instructions reviewed on 2026-09-08. The QA and release evidence at the end describes the original September 4 release, not the current container. For the current sample and deployment, see the [judge walkthrough](demo-runbook.md) and [KANAPP release record](deployment-2026-09-08-kanapp-sample.md).

RevisionProof now covers the common hackathon edit set in one review flow: zoom, text, timed subtitles, exact cuts, reviewed quiet-pause removal, speed, volume, logo overlay, and speech-to-subtitle drafting. Every time field refers to the original video. The user reviews the editable plan, creates full previews, chooses A or B, and then checks the deterministic verification result. Final delivery approval remains a separate action.

## What works

| Control | Supported behavior | Limit or review point |
|---|---|---|
| Zoom in | Fixed center punch-in for an exact interval | A 1.05×, B 1.12× |
| Add text | Literal Korean/English text at seven positions | Up to 160 characters and three lines per card |
| Timed subtitle | One editable cue per card | Manual or generated; check every word and time |
| Cut a section | Remove picture and sound for an exact interval | Result must keep at least one second |
| Find quiet pauses | Analyze audio and propose cuts | Suggestions are unchecked until selected |
| Change speed | Retimes picture and sound together | 0.5×, 0.75×, 1.25×, 1.5×, or 2×; result <=60s |
| Adjust volume | Change one audio interval | Mute or −12/−6/+3/+6/+12 dB |
| Add logo | Upload and place a logo at a corner or center | PNG/JPG/WebP, <=2 MiB, <=2048 px per side |
| Generate subtitles from speech | Draft timed cues from the selected video's audio | LIVE only; Auto, Korean, English, or Korean+English mixed |

The original video must be MP4, MOV, or WebM, 4–60 seconds, and no larger than 32 MB (32,000,000 bytes). A plan can contain at most 24 selected operations. Slow motion can lengthen the result, so the editor blocks any plan that would exceed 60 seconds.

## Use the automatic subtitles

1. Select or upload the video first, then open Studio step **2 Edits**.
2. Choose the speech language: `Detect Korean + English`, `Korean`, `English`, or `Korean + English`.
3. Select `Create captions`. This uses the configured LIVE Gemini service; it is not a fixture transcription.
4. Read every generated card. Correct names, punctuation, wording, start time, and end time.
5. Add or remove cues as needed, then select `Check plan`. The classic UI uses the labels `Generate editable subtitles` and `Review edit plan` for the equivalent steps.

The service extracts the audio and uses the configured Google Vertex Gemini runtime. It asks for only audible speech and explicitly asks the model not to translate, summarize, correct, or invent wording. The result is still a machine-generated draft. It does not become approved merely because it appeared on screen.

## Useful requests and controls

Use the cards for logo upload and automatic subtitles because those steps require the exact image or audio. Natural-language drafting can prepare the other timed values.

```text
Speed up 2–6 seconds to 1.5x.
Lower the volume by 6 dB from 0–4 seconds.
Mute the audio from 8–10 seconds.
Zoom in from 4–10 seconds and add "AI, made practical." at the bottom.
```

For a KANAPP intro, upload the logo with `Add logo`, set it to `Bottom right` for the full video, generate mixed-language subtitles if the narration switches languages, and combine those cards with the exact speed and volume intervals. Option A uses a smaller logo/text treatment and B uses a larger one.

## What still needs a full editor

Moving-object tracking, removing text already burned into footage, background replacement, detailed color grading, generated scenes, voice replacement, music generation/selection, and semantic rewriting of speech are outside this bounded renderer. The in-product `What can I ask for?` panel repeats these examples so users can decide before writing a request.

## Integrity and privacy boundaries

- Schema 3.1 freezes speed, volume, normalized logo ID/hash, every overlay, the mapped timeline, and the chosen full-preview SHA-256.
- The export is a byte-identical copy of the chosen preview. Three deterministic checks must pass before delivery can be enabled.
- Uploaded logos and in-progress runs are process-local temporary data. They can disappear after a service restart.
- LIVE transcription sends the extracted audio to the configured Google Vertex Gemini project. No synthetic transcription success is shown in FIXTURE mode.
- Generated cues remain editable and unapproved. RevisionProof does not silently apply them or translate mixed speech.
- The public demo has no tenant login. Do not use it for confidential client material.

## Historical local QA, September 4

- Desktop and 390 px mobile layouts: all eight controls are reachable, the mobile page has no horizontal overflow, and the browser console is clean.
- A 2 MiB-plus logo is rejected in the browser before upload. A valid logo is normalized, previewed, and rendered.
- A compound 10-second synthetic run combined 1.5× speed, −6 dB volume, and a full-video logo. B reached `READY` with all three checks `PASS`; output duration was 8.67 seconds and the rendered logo frame was inspected.
- The run remained unapproved for final delivery. Synthetic media was used; the local KANAPP source was not uploaded for QA.
- Code gates: backend 336/336, focused advanced/basic/tool regressions 25/25, post-rate-limit checks 5/5, and frontend 23/23 pass. Ruff, frontend ESLint, and the production build also pass.

## Historical release evidence, September 4

At that release, source `150d36774b0acaece9aad57a4d655af3eda59c5b` was deployed as revision `revisionproof-staging-00023-j7p` with 100% traffic. A LIVE mixed Korean/English run generated four editable cues, combined them with 1.5x speed, -6 dB volume, and a full-video logo, then reached `READY` with all three checks `PASS`. Final delivery approval remained false. See the [dated deployment and LIVE QA record](deployment-2026-09-04-advanced-editing.md).
