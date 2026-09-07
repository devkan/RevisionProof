# Studio: inline edit settings and softer cards

## Current state

Release update: the user subsequently authorized push and deployment. Source `8e63093` is now LIVE as `revisionproof-staging-00029-2t2` at 100% traffic. See [deployment, canary and recovery evidence](deployment-2026-09-05-inline-studio.md). The local-only statements below describe the original implementation session, not the current release status.

User request: settings directly below the selected revision, less rigid surfaces, existing three-column / six-step layout and classic page preserved. User approved saving the preceding Check plan fix as a local commit, then continuing UI work. This update is **local only: no push/deployment**.

Restore point before this redesign: `40767f6` (`fix(studio): explain blocked plans with actionable edit links`). Earlier deployment references remain in [deployment record](deployment-2026-09-05-studio.md); this document does not claim a new LIVE release.

## Changes

- `1de51ec`: one expanded settings panel directly within its revision card; open/close affordance, accessible disclosure ownership and inline validation messages. Existing edit/update/delete/duplicate/reorder contracts reused.
- `4cd35a4`: six new regression tests, no changes to existing tests or CI.
- `2a2adee`: 8px controls, 14px cards, 20px video surfaces, softer outlines, readable metadata, reduced decoration. Manrope and the charcoal/amber palette retained.
- `c59e2ca`: isolated Studio workspace sizing from classic `main` styles. At 940px viewport the prior workspace was 988px wide and clipped the right panel; it now fits exactly 940px. Existing desktop columns and mobile breakpoint unchanged.

## Verified locally

gstack design-review and hands-on browser checks used an isolated FIXTURE backend at `127.0.0.1:18131`, runtime `runtime/qa-inline-20260905`. The server was initially stopped; restarted hidden, without editing the user's in-app browser tab or its draft. Only authored demo assets were used; no external Gemini/ClickHouse calls or user video retransmission.

- All eight editor controls: zoom, text, manual captions, cut, silence, speed, volume and generated demo logo. Values persist when switching/collapsing. Checked text placement, silence 1.2s / -40dB, speed 1.25x, volume +6dB, logo top-right.
- Duplicate, reorder and delete; a single expanded editor; keyboard Enter toggles; source Watch playback and large-view Escape close.
- Original Check plan failure reproduced (zoom fully inside a cut). Visible reason -> Fix edit opens the correct inline panel -> corrected times remove the blocker and re-enable Check plan.
- Compound run `01M1RXBE3HRPBNAVE9MMZ0AHCE`: zoom 4–8s, text 4–10s, cut 0–4s. A/B previews generated; selected A; full output 26s; all three deterministic checks PASS. Step 6 displays Waiting for you. Final delivery approval/download was not executed.
- Desktop 1440x900 and 1280x720, narrow 940x900, tablet 768x1024, mobile 390x844. No horizontal overflow after the sizing fix; selected settings and bottom actions remain usable.
- Classic `/` still renders its original interface. No console errors observed on either route.
- Frontend: **69 passed / 14 files**, lint and production build passed. Backend: **349 passed**; pytest cache directory has an existing Windows write-permission warning, not a test failure.
- Final bundle: `index-BNLptUXK.js`, `index-BaYy-LUs.css`. Final sizing-only change was browser verified after the full functional run; it did not modify rendering/API code.

Evidence (generated local screenshots, ignored by Git):

- `runtime/qa-screenshots/inline-settings-before.png`
- `runtime/qa-screenshots/inline-settings-functional.png`
- `runtime/qa-screenshots/inline-settings-final-desktop.png`
- `runtime/qa-screenshots/inline-settings-final-mobile.png`
- `runtime/qa-screenshots/inline-settings-narrow-before.png`
- `runtime/qa-screenshots/inline-settings-narrow-after.png`
- `runtime/qa-screenshots/inline-settings-approval.png`

Full local design report: `C:/Users/KAN/.gstack/projects/RevisionProof/designs/design-audit-20260905/design-audit-localhost.md` (three verified findings; scoped subjective grade B -> A). No new DESIGN.md was requested or exported.

## Boundaries and continuation

- Local service is FIXTURE, not evidence of LIVE provider health. Speech-to-caption generation, smart search and external integrations were not re-exercised in this turn.
- Keep the user's existing tab/draft intact. Open `/studio` in a separate tab to load the new bundle; a page reload does not preserve this app's in-memory draft.
- Push/deployment needs the next explicit release instruction. Retain `40767f6` and existing deployment backups; use a separate checkout of that commit for comparison/restoration preparation, not a destructive reset of this working tree.
- Final human approval and approved-memory write boundaries are unchanged.
