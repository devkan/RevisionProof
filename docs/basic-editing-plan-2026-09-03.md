# Basic video editing expansion

Approved by the owner on 2026-09-03: implement zoom, literal text, timed subtitle cues, explicit cuts, and reviewed silence removal, with selectable examples and usable controls. This supersedes the previous PUNCH_IN-only product restriction. Auto-transcription, generated footage, object removal/tracking, and arbitrary effects are not in scope.

## gstack engineering review

Step 0: retain the existing upload limits, A/B approval, immutable spec, verification, official ClickHouse MCP, GCS delivery and human delivery gate. A new typed edit plan extends that pipeline; it does not create a second unaudited export path.

Architecture findings addressed in the implementation plan:
1. Old specs must still validate byte-for-byte. Introduce a distinct EDIT_PLAN candidate and schema 3.0, retaining the original candidate model/serialization for 2.x.
2. All input times refer to the original video. Resolve cuts into kept spans and map output time back to original time for comparison. Freeze the resolved operations and preview reference hash on approval.
3. Render full A/B previews for plans. A/B vary zoom strength and text styling only, never text, timing or cuts; cut-only edits need one preview. Verify exports against the approved, hashed reference and compare mapped original moments in the Change Map. Persist the corresponding reference audio baseline through existing ClickHouse feature records, distinctly labelled from legacy v1.
4. No silent partial execution. Natural-language requests produce editable structured drafts with warnings for unsupported/ambiguous items, never immediate rendering. Exact text is preserved. Guided controls work without an AI interpretation claim.
5. Silence detection measures audio amplitude, retains padding around audible sections, and proposes cuts for explicit selection before preview. No detected silence or an all-silent track must explain why no useful cut is proposed. Keep at least one second and bound segment count.

Code quality: isolate plan validation/timing, parsing, rendering and verification helpers. Reuse service locks, idempotency, upload preparation, source storage and error handling. Fixed media arguments only; user text never becomes filter syntax. Include a Korean font in the production image. Preserve legacy callers and tests.

Performance: <=24 MiB, 4–60s source, <=24 operations; sequential media execution, bounded PCM/frame extraction. Avoid repeating full render during verification; use the immutable approved full preview as the reference, check its SHA-256 before reuse. A single preview for cut-only edits prevents duplicate work.

## UX

Video -> choose edit type or example -> editable cards (original start/end, exact text, position) -> review explicit plan/detected silence -> preview appearance -> choose -> verify/download. Include a compound zoom + lower text example, successive subtitles, selected cut and quiet-pause cleanup. Explain supported operations beside inputs; failed parsing keeps the input and guided editor available. Keep advanced evidence collapsed and show actionable failures.

## Test plan

```
guided controls / natural request
  -> plan validation [unit: malformed, empty, overlap, bounds, exact text]
  -> source preparation [existing upload regressions]
  -> silence proposals [integration: leading/trailing/none/all, stereo]
  -> selected resolved operations [unit: cuts union, time mapping, empty output]
  -> A/B full preview [media: English/Korean literal text, cue boundaries, zoom, cuts]
  -> approval/hash [legacy and 3.0 tampering regressions]
  -> export verification [media: correct PASS, omitted text/wrong cut/audio tamper FAIL]
  -> LIVE feature diff / mapped Change Map [adapter regressions + fresh synthetic LIVE]
  -> playback/download [gstack desktop/mobile, errors, edit/retry]
```

Frameworks: pytest, Vitest, gstack browse. Expand the actual 614.png regression to the compound text request. Use the real KANAPP source locally; previous automatic review rejected its LIVE retransmission, so use synthetic non-sensitive media for LIVE unless the owner explicitly approves that transfer.

Implementation lanes: core plan models -> rendering/service/verification (shared backend, sequential); frontend guided composer depends on the wire contract; QA follows integration. Independent adversarial review can run alongside implementation under the gstack review workflow. No unresolved product decision requires another approval before implementing the requested scope.

Release: update docs/guardrails, run regressions and browser QA, then push/deploy using the already-authorized existing service. Preserve resources/secrets and never approve final delivery automatically.

References: [FFmpeg filter documentation](https://ffmpeg.org/ffmpeg-filters.html), current architecture and source-upload runbook. Rendering approach will be verified against actual local media, not assumed from documentation alone.
