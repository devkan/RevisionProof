#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

echo "=== project ==="
gcloud projects describe "${PROJECT_ID}" \
  --format='yaml(projectId,projectNumber,name,state,labels,createTime)'
echo "=== billing link ==="
gcloud billing projects describe "${PROJECT_ID}" \
  --format='yaml(projectId,billingAccountName,billingEnabled)'
echo "=== project-scoped billing budget ==="
gcloud billing budgets list --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
  --format='yaml(name,displayName,amount,budgetFilter,thresholdRules)'
echo "=== enabled services ==="
gcloud services list --enabled --project="${PROJECT_ID}" \
  --format='value(config.name)' | sort
echo "=== service accounts ==="
gcloud iam service-accounts list --project="${PROJECT_ID}" \
  --format='yaml(email,displayName,disabled)'
echo "=== artifact repository ==="
gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" --project="${PROJECT_ID}" \
  --format='yaml(name,format,location,labels,createTime)'
echo "=== media bucket ==="
gcloud storage buckets describe "gs://${GCS_BUCKET}" \
  --format='yaml(name,location,uniform_bucket_level_access,public_access_prevention,lifecycle_config,labels)'
echo "=== Cloud Run service (may be absent before first deploy) ==="
gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" --project="${PROJECT_ID}" \
  --format='yaml(metadata.name,status.url,spec.template.metadata.annotations,spec.template.spec.serviceAccountName)' \
  2>/dev/null || echo "not deployed"
