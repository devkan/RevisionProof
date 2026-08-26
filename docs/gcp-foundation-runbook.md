# GCP foundation runbook

This phase intentionally deploys `revisionproof-staging` in visibly labeled `FIXTURE` mode. It proves Docker, Cloud Build, Artifact Registry, GCS, IAM, and Cloud Run in a dedicated billed project without pretending that ClickHouse-backed LIVE verification is ready.

The foundation build sets `REVISIONPROOF_INSTALL_LIVE=false`, so Google ADK and ClickHouse packages are not shipped before they are usable. The guarded final `cloudbuild.yaml` explicitly installs the LIVE extras later.

## Isolation contract

- The project ID must start with `revisionproof-` and carry `managed-by=revisionproof-gcp`.
- The media bucket must be exactly `${PROJECT_ID}-media`.
- Bucket ownership is verified by listing the exact bucket within the guarded project; current `gcloud storage buckets describe --format=json` output does not expose an owner-project field.
- All commands pass `--project` explicitly; no global gcloud project is changed.
- Cloud Run uses service-level `--max=1`. Foundation deploys use service-level `--min=1` only after the credit-bearing billing account is verified.
- A project-filtered KRW 30,000 monthly budget sends alerts at 50%, 90%, and 100%. It matches the billing account currency and is an alert, not a hard spending cap.
- No ClickHouse secret or host is created in this phase.

## Provision

Run these from Google Cloud Shell after checking the active account and credit-bearing billing account:

```bash
export CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com
export CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud projects describe revisionproof-agentic-2026-kan \
  --project=revisionproof-agentic-2026-kan \
  --format='value(projectId,projectNumber)'
cp infra/gcp/foundation.env.example infra/gcp/foundation.env
# Edit the new project ID, verified credit-bearing billing account ID, budget amount, and billing currency.
bash infra/gcp/setup-foundation.sh infra/gcp/foundation.env
bash infra/gcp/inventory.sh infra/gcp/foundation.env
```

Build and deploy the staging service from the repository root:

```bash
source infra/gcp/foundation.env
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=cloudbuild.foundation.yaml \
  --gcs-source-staging-dir="gs://${GCS_BUCKET}/cloud-build-source" \
  --substitutions="_REGION=${REGION},_SERVICE=${SERVICE_NAME},_REPOSITORY=${ARTIFACT_REPOSITORY},_GCS_BUCKET=${GCS_BUCKET},_MIN_INSTANCES=${MIN_INSTANCES}" \
  .
```

The staging URL must return HTTP 200 from `/health` and `/ready`, then report `FIXTURE` and `live_ready=false` at `/api/runtime`. Do not use `z`-suffixed operational paths on Cloud Run because the platform reserves some of them. This is billed GCP infrastructure evidence, not final Gemini/ClickHouse runtime evidence.

The verified 2026-08-26 foundation deployment is Cloud Build `354696e9-0fdc-451c-9e69-cf55184ea63f`, Cloud Run revision `revisionproof-staging-00003-q56`, and URL `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`. Later builds must create a new source archive from the intended tracked commit and record its SHA-256 before submission.

The explicit source staging directory keeps future source archives in the labeled media bucket under its one-day lifecycle. The first pre-hardening build may still appear in the automatically created `${PROJECT_ID}_cloudbuild` bucket; inventory and cleanup cover that exact project-owned bucket.

Before a later LIVE deployment, set the exact ClickHouse Cloud host in the ignored `foundation.env`, then create only the two named Secret Manager secrets. The guarded script labels them, scopes access, prompts twice for each value without echoing it, and prints only numeric version IDs:

```bash
bash infra/gcp/create-live-secrets.sh \
  infra/gcp/foundation.env revisionproof-agentic-2026-kan
```

Bootstrap must pass before deployment. It creates the append-only schema and exact roles, records the project/host sentinel, uploads the source object once, seeds 768-dimensional Vertex embeddings, and verifies the expected anchor through the official MCP tool. A successful run writes only the verified host and numeric secret versions to ignored `infra/gcp/live.env`:

```bash
bash infra/gcp/bootstrap-live.sh \
  infra/gcp/foundation.env revisionproof-agentic-2026-kan
bash infra/gcp/deploy-live.sh \
  infra/gcp/foundation.env infra/gcp/live.env revisionproof-agentic-2026-kan
```

ClickHouse migration and removal are separate guarded Python commands. Cloud operations require `--confirm-project` to match the database sentinel; cleanup is dry by default and additionally requires `--execute`:

```bash
backend/.venv/bin/python scripts/migrate_clickhouse_append_only.py \
  --host "${CLICKHOUSE_HOST}" --confirm-host "${CLICKHOUSE_HOST}" \
  --confirm-project revisionproof-agentic-2026-kan --confirm revisionproof
backend/.venv/bin/python scripts/cleanup_clickhouse.py \
  --host "${CLICKHOUSE_HOST}" --confirm-host "${CLICKHOUSE_HOST}" \
  --confirm-project revisionproof-agentic-2026-kan \
  --confirm-database revisionproof
```

Never add `--execute` to ClickHouse cleanup without first reviewing the target service and deployment sentinel.

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

Cleanup is dry-run by default and refuses a project ID/number mismatch or any project without the dedicated label:

```bash
export CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com
export CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan
bash infra/gcp/cleanup.sh infra/gcp/foundation.env "${PROJECT_ID}"
```

After reviewing the inventory, the exact resource cleanup command is:

```bash
export CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com
export CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan
bash infra/gcp/cleanup.sh infra/gcp/foundation.env "${PROJECT_ID}" --execute
```

Executed resource cleanup also removes the two service accounts, the `revisionproofCloudRunDeployer` custom role, and their IAM bindings. It intentionally leaves billing linked and APIs enabled so the dedicated project can be inspected or reused; exact project deletion remains a separate manual decision.

This keeps the project and billing link for audit. Complete project deletion is a separate, explicit action and is never run by the script.
