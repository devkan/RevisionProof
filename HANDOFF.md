# Handoff

Last updated: 2026-09-08
Project: RevisionProof — `D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof`
Default branch: `main`. English documentation source: `2e764c0`, prepared in `docs/judge-facing-english-20260908`. Latest deployed application merge: `a0c589ba10a241722f6301dec68e365041039249`; documentation-only changes do not redeploy the application.

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

## Judge-Facing Documentation Review (2026-09-08)

- Used the gstack document-release workflow to compare current instructions with the shipped code, release evidence, live UI, and official rules. README and submission copy now follow the Korean narration's intent: AI drafts, code checks, and the reviewer makes the final decision.
- Corrected the missing basic-editor deployment link and mislabeled historical revisions. The English index separates the judging path from dated engineering and Korean video-production records; original attribution and historical evidence remain intact.
- Updated the submission pack to PR #3 / revision `00032-np7`, 357 backend and 82 frontend tests, and the pinned `gemini-3.5-flash-lite` setting. Removed blanket preservation/broadcast guarantees and clarified exact preview identity versus sampled diagnostics.
- Corrected architecture/security descriptions of external-file checks, current edit-plan limits, and multi-edit recipe memory. A previous statement that recipe saving was unsupported was stale; public LIVE saving is still read-only.
- Read-only checks confirmed GitHub is **PRIVATE**, the existing `main` documentation CI `34195316415` succeeded, and the live runtime reports LIVE readiness with read-only memory. This task does not make the repository public, submit Devpost, grant delivery approval, or change cloud/billing settings.
- The supplied YouTube page opened signed out in gstack with an English title/description and a displayed 3:14 duration. This confirms page access, not a new full audio/subtitle review. Official rules evaluate only the first three minutes of a longer video; the final 14 seconds cannot be relied on for judging.
- Documentation checks: 68 Markdown files, 235 relative links, zero missing targets, and no Markdown file unreachable from the root README/engineering entry points. The seven primary judge-facing documents have no Hangul characters or visible Claude/Codex name mentions (link destinations excluded for the latter). Twelve modified Markdown files rendered successfully; gstack inspected the main document preview at desktop width and confirmed no page-level horizontal overflow at 390 px. This is local Markdown-preview QA, not a claim about every historical document's prose or GitHub's own responsive styling.

## GitHub Publication Preparation (2026-09-08)

- The owner explicitly authorized pushing and merging the English documentation into `main`. Treat repository content as intended for public release, but leave the actual visibility switch to the owner.
- Repository About now uses an English product description and links directly to the live Studio. No application source, cloud settings, or repository visibility were changed for this documentation integration.
- The documentation work branch can be deleted after its commits are merged. Preserve existing backup branches and historical evidence. Do not rewrite Git history or remove attribution to imply a different development process.
- Pre-merge checks covered the judging path, 68 Markdown documents and 235 relative links. Local regression tests passed 357 backend and 82 frontend tests, with passing lint/format and frontend build. Pytest reported a local cache-write warning, not a test failure. A limited scan of tracked content and Git history found no matches for common Google/GitHub API-key formats or private-key blocks; this is not a full secrets/security audit. Local environment files and deployment credentials remain ignored.

## Earlier Work (2026-09-08 Antigravity Documentation Harmonization)

- **README.md**: Updated project description, highlighted top demo/YouTube/GitHub links, detailed the 6-step Studio workflow, and refreshed deployment information to revision `revisionproof-staging-00031-5bl` on source `b13d8b0`.
- **HANDOFF.md**: Consolidated overall completion status, added published YouTube link, and documented Antigravity's final documentation sync.
- **docs/README.md**: Re-indexed all documentation categories (Handoff, Deployment, Submission, Video & Scripts, QA Reports, Architecture) for easy navigation.
- **docs/submission-pack-2026-08-27.md**: Modernized English submission copy to reflect full 6-step Studio capabilities, partner integrations, GitHub/Demo/YouTube links, and marked Devpost submission as unconfirmed / pending owner submission.
- **docs/deployment-2026-09-07-antigravity-fixes.md**: Verified commit relationships (`dae8033` fix -> `b13d8b0` deployed source -> `a04b70b` release doc -> subsequent doc updates) and clarified that documentation commits do not alter the deployed application.
- That pass reported matching internal links and a clean `git diff --check`. The later judge-facing review found a missing basic-editor deployment target and mislabeled revision links in the index; those navigation errors are corrected in the current documentation review.

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
2. **Repository Visibility**: GitHub API reported **PRIVATE** on 2026-09-08. The owner intends public release; make it public and verify signed-out access as a separate authorized action.
3. **Video and Rights Review**: The linked video is 3:14; only its first three minutes are evaluated under the [official rules](https://agentic-cinema.devpost.com/rules). Review the evaluated portion and rights to all footage, audio, and branding. Do not mark every submission requirement complete solely because the video is uploaded.
4. **Judging Window Operations**: The rules list September 23–October 7, 2026 for judging. Keep Cloud Run and ClickHouse available. The ClickHouse runbook recorded a September 24 trial expiry as of September 3; recheck that time-sensitive state with the owner before any billing action.

## Operational Watchouts & Invariants

- **Concurrency & Single-Instance**: Cloud Run is configured with min/max 1 instance and concurrency 4. If concurrent long-running tasks occur, HTTP 429 may be returned. Keep this single-instance setting for cost control and process-local run consistency.
- **Process-Local Memory**: Runs and events live in process memory. Browser refresh does not restore the active UI session; container restart or eviction can remove the backend run. Public memory save remains read-only.
- **Cloud Project Scope**: Project `revisionproof-agentic-2026-kan` (348672234012), region `us-central1`, account `secureis@gmail.com`. Keep service accounts, secrets, and ClickHouse grants intact.
- **Rollback Reference**: Revision `revisionproof-staging-00031-5bl` remains the immediate rollback reference if ever needed.
- **Change Map Diagnostics**: Change Map samples at 2 fps (60 pairs in 30s) and serves as an inspection aid, not an exhaustive frame-by-frame verification replacement.
- **Media Invariants**: Preserved original 1080p30 footage and connected Korean speech recordings. Arial Bold (English) and Malgun Gothic Bold (Korean) are standard caption fonts.

## Suggested Next Action

Use the default-branch [English documentation index](https://github.com/devkan/RevisionProof/blob/main/docs/README.md) as the judging entry point after integration. Public repository access, video evaluation/rights review, final Devpost submission, and judging-window service continuity remain owner actions. The current English submission pack is the checklist, not proof that those separate actions have already happened. Check GitHub's PR and CI state for merge verification; do not infer it from a local branch name.
