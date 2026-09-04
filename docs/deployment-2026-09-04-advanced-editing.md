# Advanced editing LIVE release — 2026-09-04

RevisionProof now supports speed, volume, uploaded logos, and editable speech subtitles in the same review and verification flow as zoom, text, timed subtitles, cuts, and reviewed silence removal. The release was tested with synthetic Korean and English speech. The local KANAPP source video was not uploaded, and final delivery approval was not submitted.

## Source and deployment

- Application source: `150d36774b0acaece9aad57a4d655af3eda59c5b`; pushed to `origin/review/qa-hardening`.
- Existing target: `revisionproof-staging`, project `revisionproof-agentic-2026-kan` / number `348672234012`, region `us-central1`, account `secureis@gmail.com`.
- The preflight kept the existing runtime service account, 2 CPU / 4 GiB, concurrency 4, min/max instances 1, environment values, and two secret references pinned to version 1. The memory write key remains absent. No migration, billing, credential, grant, project-default, or visibility change was made.
- Source ZIP SHA-256: `aadc15728486c921885e664a2a610dd48d29ba12e40c5792d583ac71cb08ebfe`.
- Build: `fcb6b33c-7b81-421c-8d5d-21eff29cc1bf`; created `2026-09-04T03:29:43.660175540Z`, SUCCESS at `2026-09-04T03:41:32.832473Z`.
- Revision: `revisionproof-staging-00023-j7p`, traffic 100%; Ready, ConfigurationsReady, and RoutesReady are all True.
- Image digest: `sha256:fc05a5676d7a68c5c6f7502902ab81bfe2b36bff3a6bd459d144c1207344826e`.
- Browser assets: `index-ocL47ot7.js` and `index-CKklluPF.css`.
- LIVE URL: [RevisionProof advanced editing release](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=150d367).

## Exact-source quality gates

- Backend: **336 passed in 129.74s**.
- Focused advanced/basic/tool regressions: **25 passed in 22.77s**; post-rate-limit checks: **5 passed in 2.86s**.
- Frontend: **23 passed**.
- Ruff format/check, frontend ESLint, and production build passed.
- Local gstack tested all eight controls on desktop and 390 px mobile, valid and over-limit logo uploads, compound A/B previews, rendered logo visibility, zero horizontal overflow, and a clean browser console.

## Fresh LIVE gstack proof

Run `01M1N8HK13Z3R5GG8KMEEDDCYN` used a 9.963-second, 1280x720 synthetic upload containing Korean speech followed by English speech. The upload SHA-256 was `F1FCAD67D09A997FEE5403CA677342BD9F224B8384DFC3537ABA6C1749377FDB`.

1. `Korean + English mixed` transcription returned four timed cues through the LIVE Vertex integration: Korean cues plus the English phrase `AI made practical.`
2. The synthetic voice pronounced the product name ambiguously, so two generated `KANEB` fields were edited to `KANAPP`. This verified that generated cues remain editable before review.
3. The reviewed plan contained seven operations: four subtitles, 1.5x speed from 0–4 seconds, -6 dB volume from 0–4 seconds, and the uploaded logo at bottom right for the full original timeline.
4. Full A/B previews were rendered; B used the larger text and logo treatment. The original 9.93-second prepared timeline became 8.6 seconds after retiming.
5. Frozen spec **3.1** hash `36ffc486ff83343ff1384d2b77f1b15fee3505fa2745a4229ea327298bd7db61` reached **READY**. `approved_patch`, `locked_cta`, and `locked_audio` all returned **PASS**, with `publish_allowed: true`.
6. `delivery_approved` remained `false`. The final human delivery gate was deliberately left untouched.

The browser recorded successful responses for transcription (`POST /api/transcriptions` 200), logo upload (201), run creation (201), previews (200), approval/spec freeze (200), full-video generation and verification (200), evidence images (200), and generated-video playback (206). No console errors or HTTP failures occurred. At 390 px, `scrollWidth` equaled `innerWidth` and the final result card had no horizontal overflow.

Local ignored evidence includes `.gstack/advanced-live-ab-previews.png`, `.gstack/advanced-live-ready.png`, and `.gstack/advanced-live-ready-mobile.png`.

## Runtime and operating boundary

`/api/runtime` reports `LIVE`, mutable and live-ready, intelligence enabled, upload limit 24 MiB / 4–60 seconds, logo limit 2 MiB / 2048 px per side, and read-only approved-edit memory. Automatic subtitles send extracted audio to the configured Google Vertex Gemini runtime and return a draft; users must review names, punctuation, words, and timing. Runs and uploaded logo assets remain process-local and can disappear when the service restarts.

The feature is ready for hackathon use. Moving-object tracking, burned-in text removal, background replacement, generated scenes, voice replacement, and music generation remain outside this bounded renderer.
