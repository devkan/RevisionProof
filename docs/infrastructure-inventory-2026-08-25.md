# Infrastructure inventory — 2026-08-25

This file records only resources created for RevisionProof. Update it after every Docker or GCP mutation so later cleanup never relies on broad discovery.

## Local Docker

- Docker Desktop server: `29.7.2`
- Full LIVE-dependency image: `revisionproof:qa-hardening`, `sha256:0d765a900b68cdebd41c37e41a5ba01458bba7c8d543122c4f95994fef59ac89`, 2,268,448,273 bytes
- Foundation image: `revisionproof:foundation`, `sha256:e1a00fa0f9aa6d637421848e51a8ab1b087645d7dc2c2b5d17a326f6c6da9a05`, 1,145,863,104 bytes (about 49% smaller)
- Verification container: `revisionproof-local-qa-20260825`, ID `6b2944636114`, stopped after successful checks
- Foundation verification container: `revisionproof-foundation-qa-20260825`, ID `9edf6d26de58`, stopped after successful checks
- Published test ports were localhost-only: `127.0.0.1:18080` and `127.0.0.1:18081`
- Both containers returned HTTP 200 for `/healthz`, `/readyz`, and `/api/runtime`.
- Both processes ran as UID `10001` (`revisionproof`).
- Images and final containers carry `com.kanapp.managed-by=revisionproof-repo`; cleanup refuses any target without that label.
- No existing Docker image or container was removed, renamed, or stopped.

Dry-run cleanup:

```powershell
powershell -File infra/docker/cleanup-local.ps1
```

Exact labeled-target cleanup, only after review:

```powershell
powershell -File infra/docker/cleanup-local.ps1 -Execute
```

## Google Cloud

Status: **no project or resource created yet**. The internal browser reached `support@kanapp.net` but requires user reauthentication before billing credits can be verified.

Proposed isolated defaults, still pending confirmation:

- Project ID: `revisionproof-agentic-2026-kan` (must be checked for global availability)
- Region: `us-central1`
- Cloud Run service: `revisionproof-staging`
- Artifact Registry repository: `revisionproof`
- GCS bucket: `${PROJECT_ID}-media`, private, uniform access, public-access prevention, one-day lifecycle, soft delete disabled
- Runtime service account: `revisionproof-runtime`
- Build service account: `revisionproof-build`
- Cloud Run scale: min 1, max 1 after the credit-bearing billing account is confirmed
- Project-scoped budget: USD 25 alerts at 50%, 90%, and 100%; this is not a hard cap
- ClickHouse resources and secrets: not part of this foundation phase

After creation, record the exact project number, billing account ID, budget resource name, image digest, Cloud Build ID, Cloud Run revision and URL here. Use `infra/gcp/inventory.sh` as the source of truth.
