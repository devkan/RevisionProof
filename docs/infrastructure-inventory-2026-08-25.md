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

Status: **isolated project, billing, APIs, IAM, Artifact Registry, GCS, and budget verified; Cloud Build/Run deployment pending Cloud Shell CLI authentication**.

Verified in the Google Cloud Console while signed in as `secureis@gmail.com`:

- Project name: `RevisionProof Agentic 2026`
- Project ID: `revisionproof-agentic-2026-kan`
- Project number: `348672234012`
- Billing account: `0134C0-F341A5-D149BA` (the account-management project grid lists RevisionProof as linked)
- Active hackathon credit: `Marketing - All things agentic hackathon - wturney - 3 - 549836236`
- Credit ID: `UDTR8Y1KX4PPM9UC`
- Credit balance observed on 2026-08-25: `KRW 216,937.92` of `KRW 217,762.00`, expires 2026-10-24
- ScopeShift and every other existing project were left unchanged.
- Project labels saved and console-verified: `app=revisionproof`, `environment=hackathon`, `managed-by=revisionproof-gcp`.
- Enabled and console-verified APIs: Agent Platform (`aiplatform.googleapis.com`), Artifact Registry, Cloud Build, Cloud Run, Secret Manager, Billing Budgets, Cloud Billing, IAM, IAM Credentials, Logging, Monitoring, Service Usage, and Cloud Storage.
- Artifact Registry Docker repository: `projects/revisionproof-agentic-2026-kan/locations/us-central1/repositories/revisionproof`; Standard mode, labels `app=revisionproof`, `environment=hackathon`, `managed-by=revisionproof-gcp`. It is currently empty.
- GCS bucket: `gs://revisionproof-agentic-2026-kan-media`; `us-central1`, Standard, uniform bucket-level access, public-access prevention, soft delete disabled, object versioning disabled, no retention policy, and delete lifecycle for objects aged one day or more. Labels match the project.
- Runtime service account: `revisionproof-runtime@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`, unique ID `102251949493063370006`, no keys. Project roles: `roles/aiplatform.user`, `roles/logging.logWriter`. Bucket-only role: `roles/storage.objectAdmin` on the media bucket.
- Build service account: `revisionproof-build@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`, unique ID `100413539935602962847`, no keys. Project roles: `roles/artifactregistry.writer`, `roles/logging.logWriter`, `roles/run.admin`, `roles/storage.objectViewer`.
- Runtime service-account policy grants only the build service account `roles/iam.serviceAccountUser`; the console tree was expanded to verify the exact principal.
- Billing budget: `billingAccounts/0134C0-F341A5-D149BA/costViews/6e7d6d40-1b10-455a-98d3-13f100e3b233`, display name `RevisionProof revisionproof-agentic-2026-kan`; monthly KRW 30,000 alert scoped only to the RevisionProof project at 50%, 90%, and 100% actual spend. It is not a hard cap.
- Temporary private deployment source: `gs://revisionproof-agentic-2026-kan-media/revisionproof-deploy-ba10532.zip`, 194,661 local bytes (console: 194.7 KB), SHA-256 `59409F060C3B8765355A92465618BCBEB6AEB1E1E7F653BEEFAD4DE2175BAEFA`. It was generated from tracked commit `ba10532`, is not public, and the bucket lifecycle deletes it after it becomes at least one day old.
- No Cloud Build, container image, Cloud Run service/revision, or ClickHouse resource has been created yet.
- Blocker: the console session is authenticated and the Cloud Shell authorization prompt was approved, but `gcloud auth list --filter=status:ACTIVE` still reports `No credentialed accounts.` The user must complete `gcloud auth login secureis@gmail.com` directly without sharing the OAuth verification code. Cloud Shell's direct file-transfer backend failed twice, so the private lifecycle-managed GCS object above is the authenticated handoff path.

Locked isolated defaults:

- Project ID: `revisionproof-agentic-2026-kan`
- Project number guard: `348672234012`
- Region: `us-central1`
- Cloud Run service: `revisionproof-staging`
- Artifact Registry repository: `revisionproof`
- GCS bucket: `${PROJECT_ID}-media`, private, uniform access, public-access prevention, one-day lifecycle, soft delete disabled
- Runtime service account: `revisionproof-runtime`
- Build service account: `revisionproof-build`
- Cloud Run scale: min 1, max 1 after the credit-bearing billing account is confirmed
- Project-scoped budget: KRW 30,000 alerts at 50%, 90%, and 100%; this is not a hard cap
- ClickHouse resources and secrets: not part of this foundation phase

The local `infra/gcp/foundation.env` contains the exact IDs and is intentionally gitignored. `setup-foundation.sh` refuses an ID/number mismatch; the project is already labeled, so its one-time `ADOPT_EXISTING_PROJECT` switch is locked back to `NO`. The setup script is now idempotent against the console-created foundation and uses the billing account's explicit KRW currency. After deployment, record the image digest, Cloud Build ID, Cloud Run revision and URL here. Use `infra/gcp/inventory.sh` as the CLI source of truth once Cloud Shell authentication is restored.

Cloud Shell verification note: the installed gcloud rejected the combined bucket metadata update with HTTP 400. Isolated commands proved `--clear-soft-delete` and the lifecycle file succeed, while rewriting already-identical labels returns 400. CLI describe confirmed all three labels are already exact, so the script now separates metadata updates and skips the label write when current values match. No unrelated bucket was targeted.
