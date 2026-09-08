# RevisionProof Submission Pack

Updated: 2026-09-08. Sections 1–3 are the English project description; sections 4–6 are evidence and the owner's submission checklist.

The application and KANAPP sample update are deployed. **Submission is not yet confirmed:** GitHub visibility was checked as **PRIVATE** on 2026-09-08, and final Devpost submission remains unconfirmed.

- [Live Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- [Product walkthrough on YouTube](https://youtu.be/KS1vJDMnnW4), 3:14
- [Source repository](https://github.com/devkan/RevisionProof)
- [Judge walkthrough and sample instructions](demo-runbook.md)

## 1. Project Name & Tagline

**RevisionProof**

Turn video feedback into editable plans, check the result against the approved preview, and keep the final delivery decision in human hands.

## 2. Project Description

### Inspiration

A video is almost ready. Then someone asks for a closer opening shot, a corrected subtitle, or a logo at the end. Making those changes is only half the job. Someone still has to check that the result matches the request and that the rest of the video has not changed unexpectedly.

We built RevisionProof to bring that review into the editing workflow. It is for editors, producers, and people approving a revised cut who want to see what changed and understand why a result passed or was blocked.

### What It Does

RevisionProof combines editing, preview comparison, and automated checks in a six-step Studio workspace.

1. **Choose a video.** Upload a short clip or select **Use sample video** to load the same 30-second English KANAPP promo used in the walkthrough. No sample upload is needed.
2. **Prepare the edits.** Enter timecodes yourself, or ask Gemini to turn a request into an editable draft. Add zoom, text, subtitles, cuts, speed changes, volume adjustments, or a logo. The optional scene finder helps locate a moment using Google AI and ClickHouse. Speech-generated subtitles remain drafts, so you can correct a brand name or adjust the timing before using them. Quiet-pause suggestions are applied only when selected.
3. **Check the plan.** Review the edits in original-video time. The app flags conflicts, such as a caption placed entirely inside a section marked for removal, before rendering.
4. **Compare previews.** Watch A and B and choose the version you want. The app freezes the edit plan and the chosen full-preview file's SHA-256. Cut-only plans have one preview because a second would be identical.
5. **Build and verify.** The app checks whether the export matches the approved preview, whether sampled kept scenes follow the approved timeline, and whether audio levels match the approved reference within the frozen limits. You can also submit an external MP4 for checking, but a Studio plan requires an exact file match, not a visually similar re-encode. The Revision Change Map highlights windows worth reviewing and opens a synchronized original/result comparison.
6. **Make the final decision.** Passing checks make a result eligible for delivery; they do not approve it on your behalf. Review the video, then explicitly approve delivery. Failed or unavailable required checks keep delivery blocked.

In the walkthrough, an intentionally mismatched external file fails verification. We then generate the selected B preview again and check that new result. The app does not automatically repair the failed file. The video ends with final delivery approval still pending.

**RevisionProof checks the edit. You make the final call.**

### How We Built It

We separated three responsibilities: AI helps prepare a draft, deterministic code computes the checks, and a person approves the result.

- **Google AI:** Gemini on Vertex AI, coordinated with Google ADK, turns feedback into structured edits and drafts subtitle cues from speech. The optional scene finder uses descriptions and embeddings of sampled frames to help locate an edit range.
- **ClickHouse at runtime:** The official `mcp-clickhouse` server retrieves scene evidence, reads version-feature comparisons, and queries Change Map measurements and approved-edit references. Separate insert-only credentials write audit facts. MCP reads are limited to approved views.
- **Media and verification:** FFmpeg renders the bounded edits. Python and OpenCV compare the result with the frozen reference and timeline. Studio checks exact file identity, sampled visual similarity, and audio RMS/peak differences. These checks do not ask an AI model to declare PASS.
- **Workspace and hosting:** React 19, TypeScript, and Vite provide the UI; FastAPI serves the API. They run together in a Google Cloud Run container, with Cloud Storage for verified version objects, Secret Manager for credentials, and Cloud Build for deployment.
- **Reusable edit references:** ClickHouse can store verified, human-approved zooms and multi-edit recipes. Exact, HNSW, and QBit search routes are available, with the actual engine reported and exact fallback when needed. Retrieved recipes remain editable suggestions. Public saving is disabled; private saving requires a workspace key and the approval gates.

### Challenges & Learnings

**Approval needs a precise reference.** A file that looks almost right can still contain a missing caption or a different edit. For Studio plans, we freeze the chosen preview's hash and copy that exact file for export. Sampled diagnostics remain useful, but do not replace the identity check.

**Cuts and speed changes complicate comparison.** The same timestamp can refer to different moments in the source and result. We map output time back to the original timeline so reviewers can compare corresponding scenes.

**The failure path matters as much as the happy path.** QA exposed English caption wrapping, unavailable comparison playback for failed external files, and stale Change Map details after a failed result was replaced by a passing one. We fixed these paths and added regression coverage so a reviewer can inspect the failure and then see the new result clearly.

### Accomplishments & Scope Limitations

The deployed service supports the full editing and review flow. The latest sample release passed **357 backend tests and 82 frontend tests**, plus lint, build, and ClickHouse integration checks. Its public smoke test confirmed KANAPP sample playback and A/B preview generation. Earlier dated release records document successful Gemini and official MCP executions; the latest sample smoke test did not repeat those calls or grant final delivery approval.

The current scope is short-form, bounded editing: MP4/MOV/WebM sources of 4–60 seconds and up to 32 MB (32,000,000 bytes), with at most 24 selected operations. Outputs are prepared as 1280×720 H.264/AAC. Object removal, generated scenes, background replacement, and semantic correction of speech are outside scope.

Verification is limited to the approved reference and defined checks. A PASS is not a guarantee that every visual detail, word, or creative choice is correct, nor a broadcast loudness certification. Change Map samples two frame pairs per second; human playback and review still matter.

In-progress runs are process-local and are not recovered after a service restart. The public demo has no tenant login and its approved-edit library is read-only. Use the bundled sample or non-confidential footage.

## 3. Partner Integrations & Technologies

- **Partner track:** ClickHouse Cloud through the official `mcp-clickhouse` runtime server.
- **Google Cloud:** Vertex AI with Google ADK, Cloud Run, Cloud Storage, Secret Manager, and Cloud Build. The application's pinned Gemini setting is `gemini-3.5-flash-lite`; configuration alone is not evidence of a successful model call.
- **Media and application stack:** Python 3.12, FastAPI, OpenCV, Pillow, FFmpeg, React 19, TypeScript, and Vite.
- **Technical detail:** [Architecture](architecture.md), [security boundaries](security.md), and [ClickHouse runbook](clickhouse-intelligence-runbook.md).

## 4. Links & Evidence Inventory

The following identifies the application release verified on 2026-09-08. Later documentation-only commits do not change the running container.

| Evidence | Reference |
|---|---|
| Hosted application | [Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio), [classic UI](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/) |
| Product walkthrough | [YouTube, 3:14](https://youtu.be/KS1vJDMnnW4); distinct from the editable 30-second input |
| Sample source | [KANAPP provenance and checksum](../assets/demo/README.md) |
| Source merge | [PR #3](https://github.com/devkan/RevisionProof/pull/3), `a0c589b`; identical application tree to deployed archive `621423b` |
| Cloud Run | `revisionproof-staging-00032-np7`, `us-central1`, 100% traffic at the recorded check |
| Build and deployment | [KANAPP sample release record](deployment-2026-09-08-kanapp-sample.md) |
| Release CI | [PR CI](https://github.com/devkan/RevisionProof/actions/runs/34192901566), [merged-main CI](https://github.com/devkan/RevisionProof/actions/runs/34193827470), both successful |
| Prior runtime evidence | [Advanced editing and LIVE transcription](deployment-2026-09-04-advanced-editing.md), [deployed failure/recovery checks](deployment-2026-09-07-antigravity-fixes.md) |

Readiness reports configuration availability. Successful Gemini and MCP calls must be supported by the individual run trace or a dated execution record. A QA run reaching PASS is also separate from a person's final delivery approval.

## 5. Official Requirements Checkpoint

Checked against the [official rules](https://agentic-cinema.devpost.com/rules) on 2026-09-08. This is an evidence checklist, not an eligibility decision by the organizers.

| Item | Current evidence or remaining action |
|---|---|
| Working application | Hosted demo and dated deployment/QA evidence are available. Keep the service accessible during judging. |
| ClickHouse and Google Cloud runtime use | Implemented in code with dated LIVE execution records linked above. Naming a library or showing a LIVE badge alone is not execution evidence. |
| English materials | Judge-facing README, walkthrough, submission copy, and technical overview are in English. The video-production record documents English narration/subtitles; older internal records include Korean. |
| Video | The supplied YouTube page opened signed out on September 8 with an English title/description and displayed duration of 3:14. This was a page-access check, not a new full playback/subtitle review. The rules evaluate only the first three minutes of longer videos; review the evaluated portion before submitting. |
| Public source and license | Apache-2.0 [LICENSE](../LICENSE) exists. GitHub API reported **PRIVATE** on 2026-09-08. Public access is still an owner action; this item is not complete. |
| Rights to submitted media | The KANAPP sample was supplied by the owner. The owner must confirm rights to included footage, audio, and branding; bundling is not independent rights verification. |
| Devpost submission | Unconfirmed. Confirm final submission in the portal, not just a saved draft. |

## 6. Release Gates & Completion Checklist

- [x] Merge the KANAPP sample update through PR #3 (`621423b` → `a0c589b`).
- [x] Deploy revision `revisionproof-staging-00032-np7` and record the build identity.
- [x] Verify the sample checksum, seeking, public playback, and A/B preview generation.
- [x] Record passing checks: 357 backend tests, 82 frontend tests, lint/build, and release CI.
- [x] Record the supplied YouTube link and the English-subtitled 3:14 production artifact.
- [ ] Make the GitHub repository public and test source access while signed out.
- [ ] Review video access, the first-three-minutes evaluation boundary, and media rights.
- [ ] Confirm final Devpost submission before **September 9, 2026, 14:00 PDT / September 10, 06:00 KST**, per the [official rules](https://agentic-cinema.devpost.com/rules).
- [ ] Keep Cloud Run and ClickHouse available during the published judging window, September 23–October 7, 2026; recheck service/trial expiry and billing with the owner before any billing change.

See [the handoff](../HANDOFF.md) for operator continuity. No public-visibility change, Devpost submission, billing action, or final delivery approval is implied by this document.
