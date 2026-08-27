# How to record the RevisionProof demo

Target: a 2 minute 45 second English product demo, with 15 seconds of headroom. This is an operator script, **not an already recorded video or a measured end-to-end latency claim**. Use the [submission pack](submission-pack-2026-08-27.md) for the written description and release gates.

## Prepare the session

1. Open the [LIVE app](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app) in a new tab at 1440 × 900 or a similarly readable desktop size. Close account, billing, and secret-console tabs before recording. Do not click the decorative play icon in the source strip; it is not a source-video player.
2. Check [health](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/health), [readiness](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/ready), and [runtime](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/api/runtime). Require `LIVE`, healthy/ready responses, and no missing settings. Readiness alone does not prove a successful Gemini/MCP execution.
3. Have these local files ready for the native file picker:
   - `D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof\runtime\demo\revisionproof_v2_blocked.mp4`
   - `D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof\runtime\demo\revisionproof_v3_ready.mp4`
   - These are the **B / 1.12x** files. Do not choose the `_A` variants for a B-approved spec.
4. If sample files are missing in a fresh checkout, follow the [demo runbook setup](demo-runbook.md#one-time-setup). The generator intentionally recreates demo MP4s at the documented paths; do not run it against custom source media.
5. Decide who will select option B and whether that operator will approve the new final delivery. The already approved run `01M0Z3338TYVHWHK4FZRGADTKZ` is historical evidence, not authorization for a different run.
6. Keep the active app tab open throughout the flow. Reloading loses the UI's active-run selection; there is no run-restoration screen. A backend restart also loses the in-memory run. Raw JSON is not a route that restores the workflow UI.

The source MP4 contains generated geometric graphics and a synthetic tone, not a real speaking presenter. The transcript-like entries are authored scenario metadata. Keep a visible **“Synthetic demo asset · seeded scene metadata · live integrations”** caption when showing the sample.

## Paste this brief

```text
1. When the presenter says "RevisionProof," push in slightly.
2. Make the middle feel more dynamic.
3. Add B-roll that feels more premium and on-brand.
```

This is the verified seeded scenario. Do not describe it as automatic transcription of the sample clip.

## Shot list and English narration

The times below are an editing budget, not a requirement to hide real processing time. Record a complete fresh session first. If waits are trimmed, keep an on-screen **“Processing wait shortened”** caption and preserve the uncut recording for reference. Do not splice unrelated runs or replace API results.

| Time | Screen / operator action | English narration |
| --- | --- | --- |
| 00:00–00:15 | App title and LIVE badge | “A video revision can satisfy one request and still break something already approved. RevisionProof makes that approval explicit, then checks the next version against it.” |
| 00:15–00:35 | Feedback box; click **Interpret & locate evidence** once | “This controlled sample uses synthetic media and seeded scene metadata. The integrations are live. Gemini separates a precise punch-in request from a vague pacing request and unsupported B-roll creation.” |
| 00:35–00:55 | Show **AUTO PREVIEW**, **CLARIFY**, **MANUAL**, then **Anchor the evidence** and Runtime Truth | “Only the supported operation proceeds. Vertex embeddings and the official ClickHouse MCP server retrieve its time-coded evidence. Unclear or creative requests remain with the editor.” |
| 00:55–01:15 | Click **Render constrained previews**; play A and B briefly; operator clicks **Approve option B** | “Here are two constrained previews: one-point-zero-five and one-point-one-two times. I approve B. That freezes the operation, protected elements, and thresholds into a hashed revision specification.” |
| 01:15–01:55 | Show **SPEC FROZEN** / hash; **Upload MP4** → v2 file; wait for **PUBLISH BLOCKED**; show CTA frames and disabled delivery button | “The revised file includes the approved punch-in. But the protected CTA disappeared. The patch and audio-level checks pass; the CTA fails. A successful requested edit cannot override a regression, so delivery approval stays blocked.” |
| 01:55–02:20 | Save the blocked-state capture first; **Upload MP4** → v3 file; wait for **PUBLISH READY** | “The repaired version restores the CTA. All three checks now pass against the same specification. This is deterministic verification, not an AI opinion about whether the video looks good.” |
| 02:20–02:35 | **Inspect raw run JSON** in its new tab; show current run sources / hash / `delivery_approved=false`; return to app | “ClickHouse supports both evidence retrieval and the feature comparison. The passing result only enables a separate human decision. It does not publish a video.” |
| 02:35–02:45 | If explicitly chosen by the operator, click **Approve for Delivery** once and show **Approved for Delivery**. Otherwise leave the enabled button visible | With approval: “I make the final delivery decision. RevisionProof records it. Know what changed—and what stayed protected.” Without approval: “The editor keeps the final delivery decision. RevisionProof shows what changed—and what stayed protected.” |

## Capture requirements and honest claims

- Save a v2 screenshot/clip **before** uploading v3. The current run proof is replaced by v3, and earlier local proof images are pruned. The final approved run cannot recreate the earlier v2 screen.
- Record the run ID and spec hash before and after verification; they must be the same within the recorded flow.
- Show actual source labels `google.vertex.gemini` and `mcp-clickhouse.run_query`. A LIVE badge or a mock-backed test is not sufficient.
- After an operator-approved delivery decision, refresh the **raw JSON tab**, not the app tab, to capture `delivery_approved=true` and the new human approval event if needed.
- Do not claim speech recognition, automatic source-video ingestion, generated B-roll, every-frame regression coverage, semantic audio matching, external publishing, authenticated sign-off, or restart recovery.
- An old screenshot may be included only as labeled historical evidence. Do not manipulate UI state or inject the earlier run to make it appear newly executed.
- Check video pacing, readable text, English captions, audio levels, and privacy before publication. This turn did not record or upload a submission video.

## Failure and recovery cues

| Observation | Operator response |
| --- | --- |
| Non-LIVE mode or unavailable settings | Stop the LIVE recording. Do not relabel fixture output. |
| Gemini/evidence failure with **Retry preserved feedback** | Retry once in the same run after checking the error. If still failing, stop and investigate; do not imply success. |
| No safe operation or low evidence score | Show the hold/clarification accurately. For the main demonstration, start a new run with the exact brief after investigating why it differed. |
| v2 fails the patch unexpectedly | Check B was approved and the non-`_A` file was selected. Do not weaken thresholds. |
| v2 passes everything | Stop: the intended regression was not demonstrated. Verify that the actual v2 file, not v3, was uploaded. |
| Media pipeline busy or service restart | Stop this take. Do not provision another instance; the current storage design requires one owner. |
| API run returns 404 after restart/eviction | Start a new run. Do not infer that the old approval was restored from ClickHouse. |

## After recording

Keep the raw take, edited take, run ID, hash, and capture dates. Add the owner-approved public video URL to the submission pack. Publishing the video, making GitHub public, merging branches, and submitting Devpost each remain separate owner decisions.
