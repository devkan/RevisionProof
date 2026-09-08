# Handoff

Last updated: 2026-09-08
Project: RevisionProof — `D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof`
Branch: `main`. Latest deployed application merge: `a0c589ba10a241722f6301dec68e365041039249`; later documentation commits may follow.

## Core Links

- **GitHub Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)
- **Live Studio Demo**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) (Classic UI: [`/`](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/))
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)

## Current Status

- **Development, QA, and Merge**: [PR #3](https://github.com/devkan/RevisionProof/pull/3) merged the KANAPP sample change (`621423b`) into `main` as `a0c589b`. Studio's **Use sample video** now loads the exact English KANAPP walkthrough input. The original scene-search demo and all previous Antigravity QA fixes remain intact.
- **Cloud Run Deployment**: Revision `revisionproof-staging-00032-np7` is active at 100% traffic in `us-central1`. Deployed image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:1bc66b0f-a094-4f84-8215-925b518b867b`. Live health/readiness endpoints (`/health`, `/ready`) return HTTP 200 / LIVE. Before/after runtime settings and secret references match.
- **Three Antigravity Fixes Verified Live**:
  1. Word-aware English caption wrapping with character fallback for oversized tokens.
  2. Failed external video comparison enabled with synchronized dual playback.
  3. Change Map detail refresh dynamically synchronized without retaining stale BLOCKED failure objects.
- **Continuous Integration**: KANAPP PR CI `34192901566` and merged-main CI `34193827470` completed with **SUCCESS**, including quality/container and ClickHouse integration. Local checks passed 357 backend and 82 frontend tests.
- **Demo Video Completed**: English demo video (3:14) is finalized, subtitled, and published on YouTube at [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4). Local viewing copies are preserved at `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v5_subtitled.mp4` and `revisionproof_demo_final_v4_ko_v3_subtitled.mp4`.

## KANAPP Sample Update (2026-09-08)

- Bundled the owner-provided 30-second English clip without re-encoding; default selection, allowlisted media routing, Docker packaging, and immutable run-source resolution are covered by regression tests.
- Verified the public sample's exact SHA-256, HTTP 206 seeking, browser playback, and A/B previews for a 4–8 second zoom. QA run `01M1ZV6NGH6HQGXT4T0G1G6365` stopped at `PREVIEWS_READY`; no final delivery approval or public memory save.
- See the [KANAPP sample deployment record](docs/deployment-2026-09-08-kanapp-sample.md) for exact Git, build, revision, and verification evidence.

## Earlier Work (2026-09-08 Antigravity Documentation Harmonization)

- **README.md**: Updated project description, highlighted top demo/YouTube/GitHub links, detailed the 6-step Studio workflow, and refreshed deployment information to revision `revisionproof-staging-00031-5bl` on source `b13d8b0`.
- **HANDOFF.md**: Consolidated overall completion status, added published YouTube link, and documented Antigravity's final documentation sync.
- **docs/README.md**: Re-indexed all documentation categories (Handoff, Deployment, Submission, Video & Scripts, QA Reports, Architecture) for easy navigation.
- **docs/submission-pack-2026-08-27.md**: Modernized English submission copy to reflect full 6-step Studio capabilities, partner integrations, GitHub/Demo/YouTube links, and marked Devpost submission as unconfirmed / pending owner submission.
- **docs/deployment-2026-09-07-antigravity-fixes.md**: Verified commit relationships (`dae8033` fix -> `b13d8b0` deployed source -> `a04b70b` release doc -> subsequent doc updates) and clarified that documentation commits do not alter the deployed application.
- Verified that all internal document links match existing files on disk, confirmed `git diff --check`, and prepared documentation-only commit for remote push.

## Relevant Docs

- [KANAPP Sample Deployment Record](docs/deployment-2026-09-08-kanapp-sample.md) — current deployment reference.
- [Antigravity QA Fixes Deployment Record](docs/deployment-2026-09-07-antigravity-fixes.md) — previous release reference.
- [Submission Pack & Release Gates](docs/submission-pack-2026-08-27.md) — hackathon submission overview.
- [Structured Live Evidence](docs/evidence-release-20260907-results.json) and [Deployed Caption Frame](docs/evidence-release-20260907-caption-live.png).
- [Independent Final Re-Review](docs/review-2026-09-07-antigravity-supplement.md), [Antigravity Supplement](docs/fix-supplement-2026-09-07.md), [Original QA Review](docs/qa-review-2026-09-07.md), [Archived Walkthrough](docs/antigravity-walkthrough-2026-09-07.md).
- [English Subtitled Video v5](docs/demo-subtitles-2026-09-07.md), [Korean Summary Subtitles v3](docs/demo-korean-summary-subtitles-2026-09-07.md), [Korean Conversational Audio v2](docs/demo-korean-conversational-audio-2026-09-07.md).
- [ClickHouse Intelligence Runbook](docs/clickhouse-intelligence-runbook.md), [Architecture & Boundaries](docs/architecture.md), and [Documentation Index](docs/README.md).

## Remaining Work

1. **Devpost Hackathon Submission**: Final submission through the Devpost portal remains unconfirmed and is pending final owner submission before the deadline (September 9, 2026, 14:00 PDT / September 10, 06:00 KST).
2. **Repository Visibility**: Confirm repository visibility is public for judging access.
3. **Judging Window Operations**: Keep Cloud Run service and ClickHouse Cloud service active during judging.

## Operational Watchouts & Invariants

- **Concurrency & Single-Instance**: Cloud Run is configured with min/max 1 instance and concurrency 4. If concurrent long-running tasks occur, HTTP 429 may be returned. Keep this single-instance setting for cost control and process-local run consistency.
- **Process-Local Memory**: Runs and events live in process memory; browser refresh or container restart can clear active runs. Public memory save remains read-only.
- **Cloud Project Scope**: Project `revisionproof-agentic-2026-kan` (348672234012), region `us-central1`, account `secureis@gmail.com`. Keep service accounts, secrets, and ClickHouse grants intact.
- **Rollback Reference**: Revision `revisionproof-staging-00031-5bl` remains the immediate rollback reference if ever needed.
- **Change Map Diagnostics**: Change Map samples at 2 fps (60 pairs in 30s) and serves as an inspection aid, not an exhaustive frame-by-frame verification replacement.
- **Media Invariants**: Preserved original 1080p30 footage and connected Korean speech recordings. Arial Bold (English) and Malgun Gothic Bold (Korean) are standard caption fonts.

## Suggested Next Action

All project code, tests, deployments, videos, and documentation are complete and synchronized. The project is ready for final Devpost hackathon submission by the owner.
