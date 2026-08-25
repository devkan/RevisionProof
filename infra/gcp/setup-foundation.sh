#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy foundation.env.example and set the exact billing account first." >&2
  exit 2
fi

# shellcheck source=/dev/null
source "${ENV_FILE}"

required=(
  PROJECT_ID PROJECT_NAME BILLING_ACCOUNT_ID REGION ARTIFACT_REPOSITORY
  SERVICE_NAME RUNTIME_SERVICE_ACCOUNT BUILD_SERVICE_ACCOUNT GCS_BUCKET
  MIN_INSTANCES BUDGET_AMOUNT_USD BUDGET_DISPLAY_NAME
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" || "${!name}" == REPLACE_* ]]; then
    echo "Required variable ${name} is not configured." >&2
    exit 2
  fi
done

if [[ ! "${PROJECT_ID}" =~ ^revisionproof-[a-z0-9-]{6,16}$ ]]; then
  echo "PROJECT_ID must be a dedicated lowercase revisionproof-* id of at most 30 characters." >&2
  exit 2
fi
if [[ "${GCS_BUCKET}" != "${PROJECT_ID}-media" ]]; then
  echo "GCS_BUCKET must be ${PROJECT_ID}-media so cleanup cannot target an unrelated bucket." >&2
  exit 2
fi
if [[ ! "${MIN_INSTANCES}" =~ ^[01]$ ]]; then
  echo "MIN_INSTANCES must be 0 or 1 because the service is capped at one instance." >&2
  exit 2
fi
if [[ ! "${BUDGET_AMOUNT_USD}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BUDGET_AMOUNT_USD must be a positive whole-dollar alert amount." >&2
  exit 2
fi

command -v gcloud >/dev/null
command -v jq >/dev/null

managed_label="revisionproof-gcp"
if gcloud projects describe "${PROJECT_ID}" >/dev/null 2>&1; then
  existing_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
  if [[ "${existing_label}" != "${managed_label}" ]]; then
    echo "Refusing to modify existing project ${PROJECT_ID}: managed-by label is not ${managed_label}." >&2
    exit 3
  fi
else
  gcloud projects create "${PROJECT_ID}" \
    --name="${PROJECT_NAME}" \
    --labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}"
fi

expected_billing="billingAccounts/${BILLING_ACCOUNT_ID}"
current_billing="$(gcloud billing projects describe "${PROJECT_ID}" --format='value(billingAccountName)' 2>/dev/null || true)"
if [[ -n "${current_billing}" && "${current_billing}" != "${expected_billing}" ]]; then
  echo "Refusing to relink ${PROJECT_ID}: it is already attached to ${current_billing}." >&2
  exit 3
fi
if [[ "${current_billing}" != "${expected_billing}" ]]; then
  gcloud billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT_ID}"
fi

gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  billingbudgets.googleapis.com \
  cloudbilling.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  serviceusage.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
runtime_sa="${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
build_sa="${BUILD_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "${runtime_sa}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${RUNTIME_SERVICE_ACCOUNT}" \
    --display-name="RevisionProof Cloud Run runtime" \
    --project="${PROJECT_ID}"
fi
if ! gcloud iam service-accounts describe "${build_sa}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${BUILD_SERVICE_ACCOUNT}" \
    --display-name="RevisionProof Cloud Build deployer" \
    --project="${PROJECT_ID}"
fi

for role in roles/aiplatform.user roles/logging.logWriter roles/storage.objectAdmin; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${runtime_sa}" \
    --role="${role}" \
    --condition=None >/dev/null
done
for role in roles/artifactregistry.writer roles/logging.logWriter roles/run.admin roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${build_sa}" \
    --role="${role}" \
    --condition=None >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "${runtime_sa}" \
  --member="serviceAccount:${build_sa}" \
  --role="roles/iam.serviceAccountUser" \
  --project="${PROJECT_ID}" >/dev/null

if ! gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${ARTIFACT_REPOSITORY}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="RevisionProof hackathon images" \
    --labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}" \
    --project="${PROJECT_ID}"
fi

if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${GCS_BUCKET}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention \
    --soft-delete-duration=0
fi
gcloud storage buckets update "gs://${GCS_BUCKET}" \
  --lifecycle-file="infra/gcp/media-lifecycle.json" \
  --soft-delete-duration=0 \
  --update-labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}"

budget_name="$(gcloud billing budgets list \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
  --format='value(name)' \
  --limit=1)"
if [[ -z "${budget_name}" ]]; then
  budget_name="$(gcloud billing budgets create \
    --billing-account="${BILLING_ACCOUNT_ID}" \
    --display-name="${BUDGET_DISPLAY_NAME}" \
    --budget-amount="${BUDGET_AMOUNT_USD}USD" \
    --filter-projects="projects/${project_number}" \
    --threshold-rule=percent=0.50 \
    --threshold-rule=percent=0.90 \
    --threshold-rule=percent=1.00 \
    --format='value(name)')"
fi

echo "RevisionProof GCP foundation is ready."
echo "project_id=${PROJECT_ID}"
echo "project_number=${project_number}"
echo "billing_account=${BILLING_ACCOUNT_ID}"
echo "region=${REGION}"
echo "runtime_service_account=${runtime_sa}"
echo "build_service_account=${build_sa}"
echo "artifact_repository=${ARTIFACT_REPOSITORY}"
echo "gcs_bucket=${GCS_BUCKET}"
echo "budget=${budget_name} (${BUDGET_AMOUNT_USD} USD alerts; not a hard cap)"
echo "Next: run infra/gcp/inventory.sh, then submit cloudbuild.foundation.yaml."
