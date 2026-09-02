# Visual demo asset upgrade and QA — 2026-09-02

## Outcome

The generated sample is now visually inspectable. It tells a four-scene story while preserving the exact time windows and regions used by the deterministic verifier.

| Time | Visible scene | Verification purpose |
| --- | --- | --- |
| 00:00–00:08 | Editor receives and interprets client feedback | Establishes the revision workflow |
| 00:08–00:14 | Presenter reveals the centered RevisionProof card | Makes the 1.05x/1.12x punch-in visible |
| 00:14–00:24 | Source, option A, and option B comparison cards | Explains constrained alternatives |
| 00:24–00:30 | Verified delivery end card with bottom-right CTA | Makes locked-overlay failure and recovery obvious |

The approved-patch verifier still samples 00:08–00:14. The CTA verifier still samples the `840,570,340,90` region during 00:24–00:29. The test media therefore demonstrates the production rule rather than changing the rule to fit the demo.

## Evidence

Local gstack evidence is saved under `.gstack/qa-reports/screenshots/` as
`demo-storyboard-after.png`, `demo-punch-options-after.png`,
`demo-cta-variants-after.png`, `sample-video-previews-after.png`,
`sample-video-v2-blocked-after.png`, and `sample-video-v3-ready-after.png`.
The `.gstack` directory remains intentionally untracked; the reproducible source of
truth is the generator plus the visual regression test.

## Regression protection

`backend/tests/test_demo_asset_visuals.py` rejects a source that becomes visually sparse, loses scene-to-scene separation, makes A/B frames indistinguishable, fails to remove the CTA in v2, or fails to preserve it in v3.

Verification completed:

- Full backend suite: 106 passed.
- Ruff: passed.
- Frontend production build: passed.
- gstack browser QA: complete flow passed with no console errors.

## LIVE asset identity

The visual sample uses asset ID `01M00000000000000000000000` and segment IDs ending in `001`, `002`, and `003`. The prior `01J...` source and rows remain untouched for auditability. The new GCS object and ClickHouse rows must exist before deploying the code that selects the new asset ID.

## LIVE deployment and browser proof

The final deploy uses commit `81521d3`, Cloud Build `a38932bf-80ff-4b89-bdde-1353305a72ca`, image digest `sha256:e3779de18b356002910c9983c29459cd31fe8c99c2f89e5b6668030d3c5332a8`, and Cloud Run revision `revisionproof-staging-00012-dnv` with 100% traffic. `/health` and `/ready` both returned LIVE success responses.

The prior default sentence named an effect but not its required 4-8 second duration, so Gemini correctly and intermittently held it for clarification. The deployed default now requests a 6-second center `PUNCH_IN`; it does not override Gemini's classification. LIVE browser run `01M1GVQRHVVZ1TAQRWJZ1H0ACC` produced `AUTO PREVIEW`, `CLARIFY`, and `MANUAL`, retrieved three official-MCP evidence matches with the intended 00:08-00:14 scene scoring 100%, rendered visible A/B previews, and froze candidate B.

Uploading `revisionproof_v3_ready.mp4` to that run produced three deterministic PASS checks and state `READY`. GCS stored the private 966,907-byte candidate at `runs/01M1GVQRHVVZ1TAQRWJZ1H0ACC/versions/revisionproof_v3_ready.mp4`; ClickHouse contains one spec, 12 feature rows, and three check rows for this run. Delivery approval was intentionally not granted during QA.
