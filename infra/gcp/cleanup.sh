#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
CONFIRM_PROJECT="${2:-}"
MODE="${3:---dry-run}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

if [[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]; then
  echo "Pass the exact project id as argument 2: ${PROJECT_ID}" >&2
  exit 2
fi
managed_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
if [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing cleanup: ${PROJECT_ID} is not labeled managed-by=revisionproof-gcp." >&2
  exit 3
fi

cat <<EOF
Cleanup target (and no other project):
  project: ${PROJECT_ID}
  Cloud Run: ${SERVICE_NAME} in ${REGION}
  Artifact Registry: ${ARTIFACT_REPOSITORY} in ${REGION}
  GCS including all objects: gs://${GCS_BUCKET}
  service accounts: ${RUNTIME_SERVICE_ACCOUNT}, ${BUILD_SERVICE_ACCOUNT}
  project-scoped billing budget: ${BUDGET_DISPLAY_NAME}
EOF

if [[ "${MODE}" != "--execute" ]]; then
  echo "Dry run only. Re-run with '--execute' after reviewing infra/gcp/inventory.sh output."
  exit 0
fi

echo "Destructive cleanup requested for the exact labeled RevisionProof project."
while IFS= read -r budget_name; do
  [[ -n "${budget_name}" ]] && gcloud billing budgets delete "${budget_name}" --quiet
done < <(gcloud billing budgets list \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
  --format='value(name)')
gcloud run services delete "${SERVICE_NAME}" \
  --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud artifacts repositories delete "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud storage rm --recursive "gs://${GCS_BUCKET}/**" || true
gcloud storage buckets delete "gs://${GCS_BUCKET}" --quiet || true
gcloud iam service-accounts delete \
  "${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" --quiet || true
gcloud iam service-accounts delete \
  "${BUILD_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" --quiet || true

echo "Resource and project-scoped budget cleanup completed. Billing remains linked and the project remains active."
echo "For complete isolation cleanup, separately review and run:"
echo "  gcloud projects delete ${PROJECT_ID}"
