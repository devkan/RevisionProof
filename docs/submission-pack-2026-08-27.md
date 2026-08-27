# RevisionProof submission pack

Updated: 2026-08-27. Status: **draft; not submitted or published**.

Use the English copy below after the release gates in this document are resolved. For the recording, follow [How to record the RevisionProof demo](demo-recording-script-2026-08-27.md).

## Copy: project name and tagline

**Name:** RevisionProof

**Tagline:** Turn video feedback into an approved patch—and catch regressions before delivery.

## Copy: project description

### Inspiration

A client can approve one small video change without approving everything that changes alongside it. We built RevisionProof for editors and producers who need to answer two questions: did the requested revision happen, and did anything previously locked regress?

### What it does

RevisionProof turns a revision brief into a constrained, reviewable workflow. It separates supported edits from unclear requests and manual creative work. For the supported center punch-in, it retrieves time-coded evidence and renders two preview strengths. A human selects an option, freezing the approved operation and verification thresholds in a SHA-256-addressed RevisionSpec.

The editor then uploads a revised MP4. RevisionProof checks the approved punch-in, a locked call-to-action region, and audio-level limits. In our demonstration, v2 contains the approved punch-in but removes the CTA, so delivery approval is blocked. The repaired v3 passes the checks and enables a separate human delivery approval. That action records approval inside RevisionProof; it does not publish or send the video to another platform.

### How we built it

A React interface and FastAPI backend run together in a Docker container on Google Cloud Run. A Google ADK agent calls Gemini through Vertex AI to interpret feedback; Vertex embeddings support evidence retrieval. The official ClickHouse MCP server executes both the segment search and the version-feature comparison at runtime.

FFmpeg renders previews and extracts media information, while OpenCV and deterministic Python checks evaluate the frozen specification. ClickHouse stores specifications, measurements, and check results through a separate insert-only connection. Private Google Cloud Storage holds uploaded candidate videos. Gemini interprets the request; it does not decide whether a revision passes.

### Demo data and scope

This prototype uses a 30-second, programmatically generated 720p video with geometric graphics and a synthetic tone. Its scene descriptions and transcript-like entries are authored seed metadata, not speech recognition or automatic video understanding. In particular, the sample note about a presenter saying “RevisionProof” is a scenario label; the generated clip does not contain that spoken line. Gemini interpretation, embeddings, ClickHouse MCP queries, media rendering, and verification operate on this controlled sample through the LIVE path.

The supported edit is a short centered punch-in with two strengths, 1.05x and 1.12x. The prototype does not generate B-roll, edit arbitrary timelines, ingest arbitrary source libraries, or check every possible visual or audio change. The audio invariant checks RMS and peak limits, not semantic or sample-exact audio identity.

### Challenges and learnings

The most important boundary was separating AI interpretation from release authority. We froze the check parameters with the approved patch and made unavailable verification block delivery. Live testing also exposed a Cloud Run concurrency issue: a long-lived event stream occupied the only request slot. Allowing four concurrent requests while keeping one instance let event updates and mutations coexist. Another fix preserved grounding when numbered feedback arrived on one line.

### Accomplishments and next steps

We completed a credential-backed run through interpretation, official MCP retrieval, A/B approval, a blocked revision, a passing repair, and a separate human approval. The next engineering priorities are durable run recovery, authenticated project ownership, and evaluation on licensed real-world footage. Run snapshots and events currently live in process memory; persistent audit data and candidate objects do not yet restore the application after a restart.

## Copy: partner integration / built with

**Partner integration:** ClickHouse Cloud through the official `mcp-clickhouse` server for time-coded evidence retrieval and revision-feature comparisons, with Gemini on Vertex AI orchestrated through Google ADK.

**Built with:** Google Cloud Run, Vertex AI, Gemini, Google ADK, Google Cloud Storage, Secret Manager, ClickHouse Cloud, MCP, Docker, Python, FastAPI, React, TypeScript, FFmpeg, OpenCV.

## Links and evidence

- [Hosted application](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app)
- [Repository](https://github.com/devkan/RevisionProof) — **PRIVATE** at the 2026-08-27 check; not yet usable by unauthenticated judges.
- [Working branch](https://github.com/devkan/RevisionProof/tree/review/qa-hardening) — current implementation/docs; default branch is `main`.
- [Existing approved run JSON](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/api/runs/01M0Z3338TYVHWHK4FZRGADTKZ) — available on 2026-08-27, but not a durable permalink across restarts or eviction.
- [Historical full LIVE evidence](qa-report-2026-08-26-live-final.md) — deployment, timings, GCS objects, and ClickHouse row counts.
- [Current read-only smoke](qa-report-2026-08-27-submission-smoke.md) — fresh health checks and the existing approval record; not a newly executed end-to-end run.
- Demo video URL: **pending recording and owner-approved publication**.

| Fact | Evidence boundary |
| --- | --- |
| Deployed source | `d1b9a10`, as recorded in the 2026-08-26 deployment inventory; no deployment was performed on 2026-08-27 |
| Existing final run | `01M0Z3338TYVHWHK4FZRGADTKZ`; GET on 2026-08-27 returned `READY`, proof `PASS`, all three checks `PASS`, and `delivery_approved=true` |
| Real integration sources | Existing run fields: `google.vertex.gemini` and `mcp-clickhouse.run_query` |
| Durable audit evidence | One spec, 24 feature rows, six check rows, and private v2/v3 objects verified on 2026-08-26; not re-queried today |
| Human delivery decision | Event 14 at `2026-08-26T13:48:30.750541Z`; not repeated today |
| Test history | 103 backend / 4 frontend tests passed in the 2026-08-26 report; not a claim of a fresh full-suite run today |

## Official requirements checkpoint

Checked against the [official rules](https://agentic-cinema.devpost.com/rules) on 2026-08-27:

- Deadline: September 9, 2026, 14:00 PDT; September 10, 2026, 06:00 KST.
- Provide a working hosted app, English description, public source repository, detectable open-source license, and runnable instructions/assets.
- The ClickHouse track requires actual use of the official MCP server; Google Cloud packages must be called, not merely listed.
- The video should show the working app, stay within three minutes, be publicly visible on YouTube or Vimeo, and use English or English subtitles.
- AI tooling is restricted to allowed Google Cloud and selected-partner tools. The rule does not explicitly settle every development-assistant scenario. **Codex-assisted development needs organizer clarification; Gemini review/rework alone is not proof of eligibility.**

This checkpoint is not an eligibility determination. Do not claim compliance solely because the runtime uses Gemini.

## Release gates — not yet submission-ready

- [ ] Owner resolves AI-development-tool eligibility with the organizer. Do not hide the development history or claim an exclusively Gemini-built project.
- [ ] Owner approves making the repository public. Visibility has **not** been changed.
- [ ] Owner chooses how to land `review/qa-hardening` on the default branch. No PR or merge was requested or created.
- [ ] Recheck GitHub's detected license after that branch is landed. The former file contained only an Apache notice and GitHub reported `Other`; the working branch now includes the full [Apache 2.0 text](https://www.apache.org/licenses/LICENSE-2.0.txt), retaining the original copyright. The license choice is unchanged.
- [ ] Reproduce the [README quick start](../README.md#local-quick-start) in a new checkout of the exact submission commit. This clean-clone check has not been performed today. Local quick start uses FIXTURE mode, not paid LIVE credentials.
- [ ] Review repository history and packaged dependencies/media for secrets, attribution, and redistribution requirements before publication. No complete legal or history audit is claimed here.
- [ ] Decide whether to replace the synthetic scene labels with faithfully annotated licensed footage before recording. Until then, preserve the synthetic/seeded-data disclosure above.
- [ ] Record a new LIVE operator rehearsal, capture the blocked state before uploading v3, and preserve run ID/hash/evidence. Do not reuse the prior run's final approval for a new run.
- [ ] Record/export the English demo, inspect the first three minutes, and obtain owner approval to publish it.
- [ ] Keep the service usable for judging; plan for restarts and cost controls. Budget alerts do not stop billing. Do not advertise automatic recovery or production-scale concurrency.
- [ ] Owner reviews the final text and submits through Devpost. This document does not submit anything.

## Source-of-truth map

Use these files to recheck the copy after an implementation change:

- [UI and exact labels](../frontend/src/App.tsx): note classifications, candidate buttons, upload flow, proof cards, and the separate delivery button.
- [Live adapters](../backend/src/revisionproof/evidence/live.py): ADK `LlmAgent` / runner, Vertex embedding call, official MCP `run_query`, direct writer, and GCS objects.
- [Workflow service](../backend/src/revisionproof/service.py): immutable approval, persistence, fail-closed verification, and delivery event.
- [Verifier](../backend/src/revisionproof/verification/service.py): measured checks and reapplication of thresholds to MCP feature results.
- [Demo generator](../scripts/generate_demo_assets.py) and [seed metadata](../backend/src/revisionproof/bootstrap.py): synthetic media and authored scene descriptions. These do not perform transcription.
- [Vertical-flow tests](../backend/tests/test_vertical_flow.py) and [live-adapter path tests](../backend/tests/test_live_service_path.py): deterministic media behavior and mocked adapter contracts. Only the historical LIVE report proves credential-backed execution.
