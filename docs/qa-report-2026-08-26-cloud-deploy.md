# QA evidence - Cloud deployment and candidate-aware hardening, 2026-08-26

> Historical record: this report describes the earlier FIXTURE foundation. For current LIVE evidence, read `qa-report-2026-08-26-live-final.md`.

## Result

Status: **PASS for the deployed FIXTURE foundation path. LIVE remains deliberately unclaimed.**

Tracked source commit `6977747` was rebuilt, deployed, and exercised through the public Cloud Run URL. The final flow approved candidate A, froze its 1.05x patch, blocked v2 when the locked CTA disappeared, accepted repaired v3, and recorded a separate human delivery approval.

## Deployed artifact

- Project: `revisionproof-agentic-2026-kan` (`348672234012`)
- Cloud Build: `354696e9-0fdc-451c-9e69-cf55184ea63f`, `SUCCESS`
- Image: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:354696e9-0fdc-451c-9e69-cf55184ea63f`
- Image digest: `sha256:d8b4daad7107428776de4339726ba45fc32f60cee204ddf36a1d443f1cba8dfc`
- Cloud Run revision: `revisionproof-staging-00003-q56`, 100% traffic
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`

`/health` returned `status=ok`. `/ready` returned `status=ready`, `mode=FIXTURE`, `live_credentials_configured=false`, and `integration_execution_verified=false`. `/api/runtime` returned `mutable=true`, `live_ready=false`, and `Deterministic development fixtures; not live evidence`.

## gstack deployed browser path

gstack `browse` exercised run `01M0WTA2KJM0NJBBDVC2QEDWY5` against the public service:

1. The page loaded with a visible `FIXTURE MODE` badge and runtime truth panel.
2. The default brief produced one `AUTO PREVIEW`, one `CLARIFY`, and one `MANUAL` note. Only the safe note produced three fixture evidence anchors.
3. A/B previews rendered, and candidate **A** froze a 1.05x patch for `0:08-0:14` with spec hash `d6539e46736184017af3c4287c67562c5851619e1b1764b197f3cceea98c7488`.
4. v2 passed the approved punch-in and audio checks, failed the locked CTA check with zero passing frames, and rendered `PUBLISH BLOCKED`.
5. v3 passed all three checks, including five passing CTA frames, and rendered `PUBLISH READY`.
6. `Approve for Delivery` succeeded. Raw run JSON reported `state=READY`, `delivery_approved=true`, and 12 ordered events containing both the blocked and repaired transitions.

Application console errors: **0**. Failed requests: **0**. All expected media range requests returned HTTP 206, and all action requests returned HTTP 200 or 201.

Observed deployed timings from the gstack network log:

- Initial document: 251 ms
- Run creation: 319 ms
- A/B render: 4.331 s
- v2 upload and verification: 4.487 s
- v3 upload and verification: 3.204 s
- Delivery approval: 173 ms
- Browser navigation total: 910 ms

At 375x812, document `scrollWidth` equaled `clientWidth` at 375 px, no horizontal overflow was present, and no visible interactive target was smaller than 44 px.

## Automated and local container evidence

- Backend: 56 tests pass; the latest coverage run reports 79%.
- Frontend: one Vitest API regression test passes.
- Ruff check and format check pass for 33 Python files.
- ESLint and the Vite production build pass.
- Three consecutive real-media demo rehearsals pass.
- Final local image: `revisionproof:qa-final`, `sha256:7fc2c1bf5ef5fa60d29b3919d3fadd2bb747e54336d1bf9cbc2ba7350441645c`.
- The final non-root QA container passed `/health`, `/ready`, and `/api/runtime`, then was stopped and automatically removed. The image remains available.
- Independent operations/API, security, and testing reviews found no remaining P1 or P2 defects in the reviewed hardening scope.

## Deliberate limits

- Google ADK/Gemini, Vertex embedding, ClickHouse Cloud TLS, persisted ClickHouse rows, and the official MCP path against the target cloud database are still unverified.
- ClickHouse provisioning remains deferred by request. This deployment is billed GCP foundation evidence, not LIVE integration evidence.
- Run snapshots and proof traces remain process-local. A Cloud Run restart requires a new run.
- The public FIXTURE demo uses one instance-global anonymous run-creation bucket. Cost is bounded, but one caller can consume the shared allowance.
- The build service account still has project-level `roles/run.admin` for bootstrap deployment. The dedicated project limits the blast radius; a narrower conditional or custom role is follow-up hardening.

## Post-report hardening

After this historical FIXTURE QA run, the runtime bucket role was reduced from `objectAdmin` to bucket-scoped `objectCreator` plus `objectViewer`. The build service account moved from `roles/run.admin` to the project-local `revisionproofCloudRunDeployer` custom role. These IAM changes are verified in GCP, but the application source changes and LIVE integrations have not been redeployed; see [LIVE hardening progress](live-hardening-progress-2026-08-26.md).
