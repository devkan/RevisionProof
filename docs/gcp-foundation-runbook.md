# GCP foundation runbook

This phase intentionally deploys `revisionproof-staging` in visibly labeled `FIXTURE` mode. It proves Docker, Cloud Build, Artifact Registry, GCS, IAM, and Cloud Run in a dedicated billed project without pretending that ClickHouse-backed LIVE verification is ready.

The foundation build sets `REVISIONPROOF_INSTALL_LIVE=false`, so Google ADK and ClickHouse packages are not shipped before they are usable. The guarded final `cloudbuild.yaml` explicitly installs the LIVE extras later.

## Isolation contract

- The project ID must start with `revisionproof-` and carry `managed-by=revisionproof-gcp`.
- The media bucket must be exactly `${PROJECT_ID}-media`.
- All commands pass `--project` explicitly; no global gcloud project is changed.
- Cloud Run uses `max-instances=1`. Foundation deploys use `min-instances=1` only after the credit-bearing billing account is verified.
- A project-filtered USD 25 budget sends alerts at 50%, 90%, and 100%. It is an alert, not a hard spending cap.
- No ClickHouse secret or host is created in this phase.

## Provision

Run these from Google Cloud Shell after checking the active account and credit-bearing billing account:

```bash
cp infra/gcp/foundation.env.example infra/gcp/foundation.env
# Edit the new project ID, verified credit-bearing billing account ID, and budget amount.
bash infra/gcp/setup-foundation.sh infra/gcp/foundation.env
bash infra/gcp/inventory.sh infra/gcp/foundation.env
```

Build and deploy the staging service from the repository root:

```bash
source infra/gcp/foundation.env
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=cloudbuild.foundation.yaml \
  --substitutions="_REGION=${REGION},_SERVICE=${SERVICE_NAME},_REPOSITORY=${ARTIFACT_REPOSITORY},_GCS_BUCKET=${GCS_BUCKET},_MIN_INSTANCES=${MIN_INSTANCES}" \
  .
```

The staging URL must report `FIXTURE` and `live_ready=false` at `/api/runtime`. This is billed GCP infrastructure evidence, not final Gemini/ClickHouse runtime evidence.

## Inventory and modification

`infra/gcp/inventory.sh` prints the exact project, billing link, APIs, service accounts, Artifact Registry repository, bucket policy/lifecycle, and Cloud Run URL. Record its output in the dated resource inventory after every external change.

Change cost posture without rebuilding:

```bash
gcloud run services update "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --min=0
```

## Cleanup

Cleanup is dry-run by default and refuses any project without the dedicated label:

```bash
bash infra/gcp/cleanup.sh infra/gcp/foundation.env "${PROJECT_ID}"
```

After reviewing the inventory, the exact resource cleanup command is:

```bash
bash infra/gcp/cleanup.sh infra/gcp/foundation.env "${PROJECT_ID}" --execute
```

This keeps the project and billing link for audit. Complete project deletion is a separate, explicit action and is never run by the script.
