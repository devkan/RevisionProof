# RevisionProof Documentation

[Live Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio) · [Product walkthrough](https://youtu.be/KS1vJDMnnW4) · [Source repository](https://github.com/devkan/RevisionProof)

## Start here for judging

These entry points are in English. The 30-second KANAPP sample is editable input; the 3:14 YouTube video demonstrates the product.

1. [Project overview](../README.md): who RevisionProof is for, what it does, and the verification boundary.
2. [Demo walkthrough](demo-runbook.md): try **Use sample video**, review the edits, and understand the result.
3. [Submission pack](submission-pack-2026-08-27.md): project narrative, partner integrations, evidence, and outstanding submission actions.
4. [Editing guide](advanced-editing-guide-2026-09-04.md): supported controls, examples, and limits.
5. [Architecture](architecture.md) and [security policy](security.md): how AI, deterministic checks, and human approval are separated.
6. [Latest application deployment](deployment-2026-09-08-kanapp-sample.md): revision `00032-np7`, PR #3, CI, and sample playback/preview evidence.

Repository visibility and Devpost submission are tracked separately in the submission pack. A deployment record does not establish either one.

## Operator references

- [Current handoff](../HANDOFF.md): current release, remaining owner actions, and operational watchouts.
- [Integration status](integration-status.md): current entry points and clearly dated execution evidence.
- [ClickHouse intelligence runbook](clickhouse-intelligence-runbook.md): schema, private saving, backup, restore, and search verification.
- [GCP foundation runbook](gcp-foundation-runbook.md): deployment setup and infrastructure boundaries.
- [Bundled KANAPP sample](../assets/demo/README.md): input provenance, packaging, and SHA-256.
- [Engineering guardrails](../CLAUDE.md): contributor instructions, not submission copy.

## Engineering and production archive

The records below preserve the development history, including original tool attribution and Korean working notes. They describe their stated dates, not necessarily today's deployment or feature limits. They are optional background for judges, not the current getting-started path. Local Windows paths and ignored QA artifacts in these records are operator evidence references, not downloadable repository files.

### Deployment history

- [QA fixes release, September 7](deployment-2026-09-07-antigravity-fixes.md): revision `00031-5bl`, PR #2, caption wrapping and failed-result comparison fixes.
- [English placeholders, September 6](deployment-2026-09-06-english-placeholders.md): revision `00030-gnz`.
- [Inline Studio settings, September 5](deployment-2026-09-05-inline-studio.md): revision `00029-2t2`.
- [Initial Studio release and follow-up QA, September 5](deployment-2026-09-05-studio.md): revisions `00026` through `00028`, final `00028-n4z`.
- [32 MB upload limit, September 4](deployment-2026-09-04-upload-32mb.md): revision `00025-88t`.
- [Smart scene search and recipe memory, September 4](smart-scene-and-recipe-memory-2026-09-04.md): revision `00024-c9p`; Korean record.
- [Advanced editing, September 4](deployment-2026-09-04-advanced-editing.md): revision `00023-j7p`.
- [Basic editing QA fixes, September 3](deployment-2026-09-03-qa-fixes.md): revision `00022-swm`. The [original basic editing guide](basic-editing-guide-2026-09-03.md) preserves revision `00021-4fx` and earlier rollout details in Korean.
- [Source upload and memory UX, September 3](deployment-2026-09-03-source-upload.md): revision `00016-j4q`.
- [ClickHouse intelligence, September 3](deployment-2026-09-03-clickhouse-intelligence.md): revision `00015-h6b`.

### QA, design, and implementation records

- [September 7 staging QA](qa-review-2026-09-07.md) and [code QA analysis](qa-report-2026-09-07-code-qa.md).
- [Initial fixes](fix-report-2026-09-07.md), [independent review](review-2026-09-07-antigravity-fixes.md), [fix supplement](fix-supplement-2026-09-07.md), and [final re-review](review-2026-09-07-antigravity-supplement.md).
- [Main integration plan](main-integration-2026-09-07.md) and [archived Antigravity walkthrough](antigravity-walkthrough-2026-09-07.md).
- [Studio inline-setting design](studio-inline-settings-2026-09-05.md), [six-step Studio design](studio-ui-2026-09-04.md), [Studio LIVE QA](qa-live-2026-09-05-studio.md), and [Studio re-review](qa-review-2026-09-05-studio.md).
- [Basic editing plan](basic-editing-plan-2026-09-03.md), [basic editing review](qa-review-2026-09-03-basic-editor.md), and [KANAPP demo correction](kanapp-demo-fix-2026-09-03.md).
- [Source-upload design](source-upload-and-memory-ux-2026-09-03.md), [intelligence plan](clickhouse-intelligence-plan-2026-09-03.md), and [intelligence QA](qa-report-2026-09-03-clickhouse-intelligence.md).
- [MCP recovery QA](qa-report-2026-09-02-mcp-recovery.md), [visual demo asset QA](qa-report-2026-09-02-visual-demo-asset.md), and [automatic full-video QA](qa-report-2026-09-02-automatic-full-video-ui.md).
- [September 3 handoff](handoff-2026-09-03.md), [submission smoke test](qa-report-2026-08-27-submission-smoke.md), and [original recording script](demo-recording-script-2026-08-27.md).
- [August 26 final LIVE QA](qa-report-2026-08-26-live-final.md), [cloud deployment QA](qa-report-2026-08-26-cloud-deploy.md), and [hardening progress](live-hardening-progress-2026-08-26.md).
- [August 25 QA](qa-report-2026-08-25.md), [hardening QA](qa-report-2026-08-25-v2-hardening.md), and infrastructure inventories for [August 25](infrastructure-inventory-2026-08-25.md) and [August 26](infrastructure-inventory-2026-08-26.md).

### Video and narration production

The public viewing link is [YouTube](https://youtu.be/KS1vJDMnnW4). The following are production records, many in Korean, and may refer to local media outside Git.

- [English-subtitled v5, 3:14](demo-subtitles-2026-09-07.md): subtitle design, media checksum, and QA.
- [Korean summary subtitles v3](demo-korean-summary-subtitles-2026-09-07.md), [conversational audio v2](demo-korean-conversational-audio-2026-09-07.md), and [conversational script v2](demo-narration-ko-conversational-v2-2026-09-07.md).
- [Earlier Korean audio alignment](demo-korean-audio-sync-2026-09-07.md) and [earlier Korean narration](demo-narration-ko-2026-09-07.md).
- [Final v4 timeline](demo-final-video-2026-09-06.md), [18-second introduction](demo-intro-edit-2026-09-06.md), [English audio alignment](demo-audio-sync-2026-09-06.md), [English narration timeline](demo-narration-timeline-2026-09-06.md), and [silent visual edit](demo-visual-edit-2026-09-06.md).
- [KANAPP 30-second English input and recording scenario](kanapp-english-demo-video-2026-09-04.md).
