# Inline Studio settings: push, deployment and LIVE canary

Status: **DEPLOYED AND VERIFIED**, 2026-09-05 KST. The user explicitly requested push, then deployment. This supersedes the local-only release boundary in [the implementation report](studio-inline-settings-2026-09-05.md).

## Release identity

| Item | Verified value |
| --- | --- |
| Source | `8e630931e3504468735e789db202f45bf14fe1da` |
| Remote branch | `origin/review/qa-hardening` in the existing PRIVATE repository |
| Service | `revisionproof-staging`, `us-central1` |
| Project | `revisionproof-agentic-2026-kan`, number `348672234012` |
| Cloud Build | `7ec59d25-6506-4953-b0f3-970455c263f8`, SUCCESS |
| Build start / finish | `2026-09-05T14:22:21.719066860Z` / `2026-09-05T14:28:41.137979Z` |
| Ready revision | `revisionproof-staging-00029-2t2`, 100% traffic |
| Image digest | `sha256:5b0dac0ce3d7958f1201f70be1e7065274df7e48d31b06fe4b59c2757323df7e` |
| Browser JS / CSS | `index-BNLptUXK.js` / `index-BaYy-LUs.css` |
| Source archive SHA-256 | `41bada75eca52a97554e77dc7285416f494a3f08e73e882435d235e3cab8ecca` |

[LIVE Studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio), [classic UI](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/), [Cloud Build](https://console.cloud.google.com/cloud-build/builds/7ec59d25-6506-4953-b0f3-970455c263f8?project=348672234012).

Source was archived directly from the pushed commit, uploaded through the authenticated Cloud Shell file chooser, and independently SHA-256 verified before extraction. Existing `cloudbuild.yaml` was submitted with the existing runtime/build service accounts, resource limits, bucket, ClickHouse host, global Vertex location, Gemini model, and secret versions 1/1. No IAM expansion, data migration, secret-value inspection, default-project change, PR, merge or visibility change was performed.

gstack `land-and-deploy` was adapted to the repository's established direct Cloud Build release path. Its PR/merge steps were not executed. gstack `browse` supplied the final LIVE canary. Hosted GitHub CI does not trigger for this branch push; local tests and Cloud Build success are separate evidence.

## Gates and observed LIVE behavior

- Fresh local release gates: frontend **69 passed / 14 files**, ESLint PASS; backend **349 passed in 132.10s**, using an isolated pytest cache with no cache warning. `git diff --check` clean. The production build ran in Cloud Build; its deployed asset names match the locally verified final bundle.
- Cloud Run `Ready`, `ConfigurationsReady`, and `RoutesReady` are all True. `/health`, `/ready`, and `/api/runtime` returned HTTP 200. Runtime is LIVE, with no missing settings, 32,000,000-byte source limit, intelligence enabled, and approved-memory policy `read_only`.
- `/studio` loaded the actual new bundle and real UI. Browser load was **586 ms**; classic `/` was **534 ms**. These are one-run browser navigation timings, not performance percentiles.
- In a separate gstack browser tab using the authored built-in sample, added Cut 0–4s and Zoom 0–4s. Both cards showed `needs fix`; the footer and inline panel explained that Edit 2 falls entirely inside footage removed by Edit 1, with concrete repair options and `Fix edit 2`.
- Opened the other card, then clicked the footer's `Fix edit 2`: the correct Zoom card expanded, the other panel collapsed, and focus moved to the settings checkbox. The panel is a region owned by its containing revision list item, directly below the header.
- Changed Zoom to 4–8s: warning cleared, status became READY, and `Check plan (2)` became enabled. Collapsing and reopening with Enter preserved both values.
- Desktop 1440x900, narrow 940x900 and mobile 390x844 were visually checked. The 940px workspace fits 940px exactly; document scroll width matches viewport at 940 and 390. Rounded cards, inline settings and fixed bottom actions remain present. Classic UI still renders separately.
- No browser console errors; observed LIVE page/assets/runtime/sample requests returned 200/206, with no observed failed LIVE requests.

This post-deploy canary exercised client-side edit/validation recovery, not a new LIVE render or paid speech/search request. The earlier full compound **FIXTURE** render and eight-control regression evidence remains in the implementation report. `/ready` explicitly returns `integration_execution_verified=false`: configuration readiness is not evidence of new successful provider calls. No user media upload, final delivery approval or Approved Edit Memory write was performed.

Generated screenshot evidence is local and ignored by Git:

- `runtime/qa-screenshots/inline-live-desktop-20260905.png`
- `runtime/qa-screenshots/inline-live-narrow-20260905.png`
- `runtime/qa-screenshots/inline-live-mobile-20260905.png`
- `runtime/qa-screenshots/inline-live-mobile-card-20260905.png` (annotated)

The initial whole-page annotation command encountered a gstack multiple-selector error; a scoped card annotation succeeded. This was a browser-tool annotation failure, not an application error. All saved screenshots were opened and visually inspected.

## Recovery points

Before deployment, created and pushed **`backup/pre-inline-studio-20260905`** at **`44cc8c0a4f4d1c8cb4fa66badc9aa96b3e14bcac`**, the previous LIVE source. Verified the remote ref. Previous LIVE revision **`revisionproof-staging-00028-n4z`** was healthy at 100% before rollout and is the rollback target. Existing backups `backup/pre-studio-ui-20260904` (`270d37d`) and `backup/pre-studio-reqa-20260905` (`ca87a05`) remain intact. Local pre-card-redesign checkpoint `40767f6` remains reachable in the pushed branch.

Cloud Shell service export, containing secret references rather than secret values, was saved before deployment at `/home/secureis/revisionproof-before-inline-8e63093.yaml`. Source zip is retained at `/home/secureis/revisionproof-deploy-8e63093.zip` and local `runtime/revisionproof-deploy-8e63093.zip`; neither is published to Git.

Rollback command below is documented, **not executed**. Run only after owner approval and rechecking the exact project, identity and target revision:

```sh
gcloud run services update-traffic revisionproof-staging \
  --project=revisionproof-agentic-2026-kan --region=us-central1 \
  --to-revisions=revisionproof-staging-00028-n4z=100
```

For source comparison/restoration preparation, use a separate checkout of the backup branch, never a destructive reset of the active worktree. Runs and drafts remain process-local; rollback does not restore in-memory runs. The user's active local `/studio` draft tab was not reloaded or modified. Open the LIVE URL in a separate tab to view this release safely.

Documentation committed after this release does not change the deployed source identity above.
