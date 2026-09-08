# RevisionProof Submission Pack

- **Updated**: 2026-09-08 (Final Hackathon Release)
- **Status**: **Deployment & verification complete; Devpost submission unconfirmed (pending owner final submission)**.
- **Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)
- **Live Demo**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)

---

## 1. Project Name & Tagline

- **Name**: RevisionProof
- **Tagline**: Turn video revision feedback into verified edits—and mathematically prove protected content stayed untouched before delivery.

---

## 2. Project Description

### Inspiration

When client or editorial feedback arrives on a near-final cut, making one small change often causes unintended collateral damage: a graphics layer shifts off-screen, a call-to-action (CTA) disappears, or audio levels clip.

We built **RevisionProof** for video editors, post-production teams, and producers who need to answer two definitive questions before delivering revised video:
1. **Did the requested revision actually happen at the right place and time?**
2. **Did anything previously locked, protected, or balanced regress?**

---

### What It Does

RevisionProof bridges natural-language editorial briefs with deterministic verification in a guided **6-Step Studio Workflow**:

1. **01 · Upload / Select Source**: Accepts MP4, MOV, or WebM video (up to 32 MB and 4–60 seconds), or loads pre-packaged reference assets such as our 30-second English promo.
2. **02 · Edits & AI Drafting**: Supports a rich suite of bounded video operations:
   - Center punch-in zoom (subtle 1.05× vs. punchy 1.12×)
   - Text overlays and titles
   - Speech-transcribed subtitles (Korean, English, or mixed speech via Gemini transcription)
   - Exact interval cuts and quiet-pause / silence removal
   - Speed adjustments (0.5× to 2.0×) and volume leveling (−60 dB to +12 dB)
   - Watermark / logo branding overlay
   - Natural-language feedback parsing using Google Gemini into editable, structured revision items.
3. **03 · Check Plan**: Automatically validates timecodes against source footage, catching overlapping edits or out-of-bounds operations before rendering.
4. **04 · Compare A/B Previews**: Generates synchronized candidate previews side-by-side. The user chooses an approved version, freezing the specification and its SHA-256 hash (Spec 3.1).
5. **05 · Check & Verify**: Builds the full export or audits an externally uploaded edited file against three automated gates:
   - **Approved Edit Verification**: Mathematically confirms visual changes occurred within the planned time range.
   - **Protected Region Invariants**: Confirms designated call-to-action (CTA) banners and brand marks remained 100% unaltered.
   - **Audio Invariant Limits**: Ensures peak decibel levels stay within safe broadcast margins.
   - **Revision Change Map**: Samples 2 frame pairs per second across the full video, mapping requested, unchanged, and review-needed seconds, complete with an interactive side-by-side comparison player.
6. **06 · Approve & Deliver**: A dedicated human-in-the-loop gate. Only an explicit human decision unlocks final delivery download and audit persistence.

---

### How We Built It

RevisionProof is built with a principled separation of concerns: **AI interprets and drafts; deterministic code checks and verifies; humans approve.**

- **AI & Orchestration**: Google Gemini on Vertex AI orchestrated with Google Agent Development Kit (ADK) translates conversational feedback into structured edit operations and drafts multi-language subtitle cues from speech.
- **Partner Integration — ClickHouse Cloud via Official MCP**:
  - The official `mcp-clickhouse` server runs in production to execute segment evidence retrieval, version feature comparisons, and historical edit memory searches.
  - Supports exact, HNSW, and QBit vector similarity search over previously approved edit recipes, providing reference context without delaying the active workflow.
- **Media Engine & Deterministic Checks**: Python 3.12, OpenCV, and FFmpeg compute exact pixel differences, structural similarity, and audio RMS levels against frozen spec thresholds. AI never grades its own homework.
- **Frontend Workspace**: React 19, TypeScript, and Vite deployed together with a FastAPI backend inside a container on **Google Cloud Run**.
- **Cloud Infrastructure**: Google Cloud Run, Cloud Storage (GCS), Secret Manager, Cloud Build, and ClickHouse Cloud.

---

### Challenges & Learnings

1. **Separating Generative AI from Release Authority**: Ensuring that AI assists in drafting and transcription, but cannot self-declare a check as "PASS". All pass/fail verdicts are computed strictly by mathematical thresholds in deterministic Python.
2. **Synchronized Comparative Diagnostics**: Building the 2 fps Revision Change Map with dual-player seeking so editors can visually inspect anomalies without having to watch the entire clip repeatedly.
3. **Continuous Integration & Quality Hardening**: Solving real-world rendering and state challenges during QA—such as word-aware English caption wrapping, external-video blob inspection, and dynamic state cache invalidation in React across BLOCKED → PASS transitions.

---

### Accomplishments & Scope Limitations

- **Accomplishments**:
  - End-to-end working service deployed on Google Cloud Run with verified LIVE ClickHouse Cloud MCP and Gemini Vertex AI integration.
  - Complete automated test suite: **353 backend pytest cases** and **78 frontend Vitest cases** with 100% pass rate.
  - Real-world 30-second English promo video (`kanapp_promo_english_editable_30s.mp4`) demonstrated and verified in a comprehensive 3-minute-14-second video.
- **Current Limitations**:
  - Editing is bounded to deterministic transformation (zoom, text, subtitles, cuts, speed, volume, logo); arbitrary generative B-roll synthesis or in-painting objects into footage is deliberately outside the current scope.
  - Active runs are kept in process memory; public past edit memory operates in read-only mode to prevent public pollution.

---

## 3. Partner Integrations & Technologies

- **ClickHouse Cloud & Official MCP**: `mcp-clickhouse` server for vector/exact segment search, edit memory retrieval, and revision feature comparison.
- **Google Cloud Platform**: Cloud Run, Vertex AI (Gemini 2.5), Google ADK, Cloud Storage, Secret Manager, Cloud Build.
- **Core Languages & Libraries**: Python 3.12, FastAPI, OpenCV, Pillow, FFmpeg, React 19, TypeScript, Vite.

---

## 4. Links & Evidence Inventory

- **Live Application**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- **Classic UI**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/)
- **Source Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)
- **Active Cloud Run Revision**: `revisionproof-staging-00031-5bl` (Region: `us-central1`, 100% traffic)
- **Deployed Application Source**: `b13d8b0` (merged PR #2)
- **CI Workflows**:
  - PR #2 CI: `34119684596` — SUCCESS
  - Deployed Main CI: `34120899603` — SUCCESS
  - Release Record CI: `34122820916` — SUCCESS

---

## 5. Official Hackathon Requirements Checkpoint

Checked against [Agentic Cinema Hackathon Official Rules](https://agentic-cinema.devpost.com/rules):

| Requirement | Project Status | Details |
|---|---|---|
| Working Hosted Application | **VERIFIED** | Live on Cloud Run (`revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio`) |
| Partner Track (ClickHouse) | **VERIFIED** | Official `mcp-clickhouse` used for segment search & feature comparisons |
| Google Cloud AI Tools | **VERIFIED** | Gemini on Vertex AI orchestrated via Google ADK |
| Demonstration Video | **VERIFIED** | Public on YouTube at [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4) (3:14, English narration & subtitles) |
| Open Source License | **VERIFIED** | Apache License, Version 2.0 (`LICENSE`) |
| Source Repository | **VERIFIED** | [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof) |
| Devpost Submission | **UNCONFIRMED** | Pending final owner review and submission on Devpost portal |

---

## 6. Release Gates & Completion Checklist

- [x] Merge fix branch into `main` via PR #2 (`dae8033` -> `b13d8b0`).
- [x] Deploy to Google Cloud Run (`revisionproof-staging-00031-5bl`).
- [x] Verify live health, readiness, and all three bug fixes (caption wrap, external video comparison, Change Map transition).
- [x] Verify full test suites (353 backend pytest, 78 frontend Vitest, 0 lint errors, clean build).
- [x] Record, edit, subtitle, and publish demo video to YouTube ([https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)).
- [x] Synchronize all project documentation, README, and handoff records.
- [ ] Owner final review and submission through the Devpost portal before the deadline (September 9, 2026, 14:00 PDT / September 10, 06:00 KST).
- [ ] Confirm public visibility of the GitHub repository.
- [ ] Maintain service uptime during the judging window.
