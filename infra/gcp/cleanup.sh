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

if [[ "${RUNTIME_SERVICE_ACCOUNT}" != "revisionproof-runtime" ]] \
  || [[ "${BUILD_SERVICE_ACCOUNT}" != "revisionproof-build" ]]; then
  echo "Refusing cleanup: unexpected RevisionProof service-account name." >&2
  exit 2
fi
if [[ "${PROJECT_ID}" != revisionproof-* ]]; then
  echo "Refusing cleanup: PROJECT_ID must start with revisionproof-." >&2
  exit 2
fi
if [[ "${SERVICE_NAME}" != "revisionproof-staging" ]]; then
  echo "Refusing cleanup: unexpected Cloud Run service ${SERVICE_NAME}." >&2
  exit 2
fi
if [[ "${ARTIFACT_REPOSITORY}" != "revisionproof" ]]; then
  echo "Refusing cleanup: unexpected Artifact Registry repository ${ARTIFACT_REPOSITORY}." >&2
  exit 2
fi
if [[ "${GCS_BUCKET}" != "${PROJECT_ID}-media" ]]; then
  echo "Refusing cleanup: GCS_BUCKET must be ${PROJECT_ID}-media." >&2
  exit 2
fi
if [[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]; then
  echo "Pass the exact project id as argument 2: ${PROJECT_ID}" >&2
  exit 2
fi
actual_project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]]; then
  echo "Refusing cleanup: expected project number ${EXPECTED_PROJECT_NUMBER}, got ${actual_project_number}." >&2
  exit 3
fi
managed_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
if [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing cleanup: ${PROJECT_ID} is not labeled managed-by=revisionproof-gcp." >&2
  exit 3
fi

resource_exists() {
  local output status
  if output=$("$@" 2>&1); then
    return 0
  else
    status=$?
  fi
  if grep -Eqi 'NOT_FOUND|not found|does not exist' <<<"${output}"; then
    return 1
  fi
  printf '%s\n' "${output}" >&2
  exit "${status}"
}

service_exists=false
if resource_exists gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" --project="${PROJECT_ID}" --format=json; then
  service_exists=true
  service_json="$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" --project="${PROJECT_ID}" --format=json)"
  if ! jq -e '.metadata.labels.app == "revisionproof"
    and .metadata.labels.environment == "hackathon"
    and .metadata.labels["managed-by"] == "revisionproof-gcp"' \
    <<<"${service_json}" >/dev/null; then
    echo "Refusing cleanup: Cloud Run service labels do not match RevisionProof." >&2
    exit 3
  fi
fi

repository_exists=false
if resource_exists gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" --project="${PROJECT_ID}" --format=json; then
  repository_exists=true
  repository_json="$(gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
    --location="${REGION}" --project="${PROJECT_ID}" --format=json)"
  if ! jq -e '.format == "DOCKER"
    and .labels.app == "revisionproof"
    and .labels.environment == "hackathon"
    and .labels["managed-by"] == "revisionproof-gcp"' \
    <<<"${repository_json}" >/dev/null; then
    echo "Refusing cleanup: Artifact Registry repository metadata does not match." >&2
    exit 3
  fi
fi

media_bucket_exists=false
if resource_exists gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=json; then
  media_bucket_exists=true
  bucket_json="$(gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=json)"
  bucket_owner_match="$(gcloud storage buckets list \
    --project="${PROJECT_ID}" \
    --filter="name=${GCS_BUCKET}" \
    --format='value(name)')"
  if [[ "${bucket_owner_match}" != "${GCS_BUCKET}" ]] \
    || ! jq -e '.labels.app == "revisionproof"
      and .labels.environment == "hackathon"
      and .labels["managed-by"] == "revisionproof-gcp"' \
      <<<"${bucket_json}" >/dev/null; then
    echo "Refusing cleanup: media bucket ownership or labels do not match." >&2
    exit 3
  fi
fi

default_build_bucket="${PROJECT_ID}_cloudbuild"
writer_secret="${CLICKHOUSE_WRITER_SECRET:-revisionproof-clickhouse-writer-password}"
mcp_secret="${CLICKHOUSE_MCP_SECRET:-revisionproof-clickhouse-mcp-password}"
build_bucket_exists=false
if resource_exists gcloud storage buckets describe "gs://${default_build_bucket}" --format=json; then
  build_bucket_exists=true
  build_bucket_owner_match="$(gcloud storage buckets list \
    --project="${PROJECT_ID}" \
    --filter="name=${default_build_bucket}" \
    --format='value(name)')"
  if [[ "${build_bucket_owner_match}" != "${default_build_bucket}" ]]; then
    echo "Refusing cleanup: default Cloud Build bucket belongs to another project." >&2
    exit 3
  fi
fi

for secret_name in "${writer_secret}" "${mcp_secret}"; do
  if resource_exists gcloud secrets describe "${secret_name}" \
    --project="${PROJECT_ID}" --format=json; then
    secret_json="$(gcloud secrets describe "${secret_name}" \
      --project="${PROJECT_ID}" --format=json)"
    if ! jq -e '.labels.app == "revisionproof"
      and .labels.environment == "hackathon"
      and .labels["managed-by"] == "revisionproof-gcp"' \
      <<<"${secret_json}" >/dev/null; then
      echo "Refusing cleanup: secret ${secret_name} lacks RevisionProof labels." >&2
      exit 3
    fi
  fi
done

cat <<EOF
Cleanup target (and no other project):
  project: ${PROJECT_ID}
  Cloud Run: ${SERVICE_NAME} in ${REGION}
  Artifact Registry: ${ARTIFACT_REPOSITORY} in ${REGION}
  GCS including all objects: gs://${GCS_BUCKET}
  legacy Cloud Build source bucket: gs://${default_build_bucket}
  future LIVE secrets if labeled: ${writer_secret}, ${mcp_secret}
  service accounts: ${RUNTIME_SERVICE_ACCOUNT}, ${BUILD_SERVICE_ACCOUNT}
  project-scoped billing budget: ${BUDGET_DISPLAY_NAME}
EOF

if [[ "${MODE}" != "--execute" ]]; then
  echo "Dry run only. Re-run with '--execute' after reviewing infra/gcp/inventory.sh output."
  exit 0
fi

remove_all_objects() {
  local bucket_pattern="$1" output status
  if output="$(gcloud storage ls --recursive "${bucket_pattern}" 2>&1)"; then
    if [[ -n "${output}" ]]; then
      gcloud storage rm --recursive "${bucket_pattern}"
    fi
    return
  else
    status=$?
  fi
  if grep -Eqi 'matched no objects|no URLs matched|not contain any objects' <<<"${output}"; then
    return
  fi
  printf '%s\n' "${output}" >&2
  exit "${status}"
}

echo "Destructive cleanup requested for the exact labeled RevisionProof project."
runtime_sa="${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
build_sa="${BUILD_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
runtime_member="serviceAccount:${runtime_sa}"
build_member="serviceAccount:${build_sa}"
project_policy="$(gcloud projects get-iam-policy "${PROJECT_ID}" --format=json)"

project_binding_exists() {
  local member="$1" role="$2"
  jq -e --arg member "${member}" --arg role "${role}" \
    'any(.bindings[]?; .role == $role and any(.members[]?; . == $member))' \
    <<<"${project_policy}" >/dev/null
}

while IFS= read -r budget_name; do
  [[ -n "${budget_name}" ]] && gcloud billing budgets delete "${budget_name}" --quiet
done < <(gcloud billing budgets list \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
  --format='value(name)')
if [[ "${service_exists}" == true ]]; then
  gcloud run services delete "${SERVICE_NAME}" \
    --region="${REGION}" --project="${PROJECT_ID}" --quiet
fi
if [[ "${repository_exists}" == true ]]; then
  gcloud artifacts repositories delete "${ARTIFACT_REPOSITORY}" \
    --location="${REGION}" --project="${PROJECT_ID}" --quiet
fi
if [[ "${media_bucket_exists}" == true ]]; then
  remove_all_objects "gs://${GCS_BUCKET}/**"
  gcloud storage buckets delete "gs://${GCS_BUCKET}" --quiet
fi
if [[ "${build_bucket_exists}" == true ]]; then
  remove_all_objects "gs://${default_build_bucket}/**"
  gcloud storage buckets delete "gs://${default_build_bucket}" --quiet
fi

for secret_name in "${writer_secret}" "${mcp_secret}"; do
  if resource_exists gcloud secrets describe "${secret_name}" \
    --project="${PROJECT_ID}" --format=json; then
    gcloud secrets delete "${secret_name}" --project="${PROJECT_ID}" --quiet
  fi
done

for role in roles/aiplatform.user roles/logging.logWriter; do
  if project_binding_exists "${runtime_member}" "${role}"; then
    gcloud projects remove-iam-policy-binding "${PROJECT_ID}" \
      --member="${runtime_member}" --role="${role}" \
      --condition=None --quiet >/dev/null
  fi
done
for role in roles/artifactregistry.writer roles/logging.logWriter roles/run.admin roles/storage.objectViewer; do
  if project_binding_exists "${build_member}" "${role}"; then
    gcloud projects remove-iam-policy-binding "${PROJECT_ID}" \
      --member="${build_member}" --role="${role}" \
      --condition=None --quiet >/dev/null
  fi
done

runtime_sa_exists=false
if resource_exists gcloud iam service-accounts describe "${runtime_sa}" \
  --project="${PROJECT_ID}" --format=json; then
  runtime_sa_exists=true
  runtime_policy="$(gcloud iam service-accounts get-iam-policy "${runtime_sa}" \
    --project="${PROJECT_ID}" --format=json)"
  if jq -e --arg member "${build_member}" \
    'any(.bindings[]?; .role == "roles/iam.serviceAccountUser"
      and any(.members[]?; . == $member))' <<<"${runtime_policy}" >/dev/null; then
    gcloud iam service-accounts remove-iam-policy-binding "${runtime_sa}" \
      --member="${build_member}" --role="roles/iam.serviceAccountUser" \
      --project="${PROJECT_ID}" --quiet >/dev/null
  fi
fi
build_sa_exists=false
if resource_exists gcloud iam service-accounts describe "${build_sa}" \
  --project="${PROJECT_ID}" --format=json; then
  build_sa_exists=true
fi
if [[ "${runtime_sa_exists}" == true ]]; then
  gcloud iam service-accounts delete "${runtime_sa}" --project="${PROJECT_ID}" --quiet
fi
if [[ "${build_sa_exists}" == true ]]; then
  gcloud iam service-accounts delete "${build_sa}" --project="${PROJECT_ID}" --quiet
fi

remaining_budget="$(gcloud billing budgets list \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" --format='value(name)')"
if [[ -n "${remaining_budget}" ]] \
  || resource_exists gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" --project="${PROJECT_ID}" --format=json \
  || resource_exists gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
    --location="${REGION}" --project="${PROJECT_ID}" --format=json \
  || resource_exists gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=json \
  || resource_exists gcloud storage buckets describe "gs://${default_build_bucket}" --format=json \
  || resource_exists gcloud secrets describe "${writer_secret}" \
    --project="${PROJECT_ID}" --format=json \
  || resource_exists gcloud secrets describe "${mcp_secret}" \
    --project="${PROJECT_ID}" --format=json \
  || resource_exists gcloud iam service-accounts describe "${runtime_sa}" \
    --project="${PROJECT_ID}" --format=json \
  || resource_exists gcloud iam service-accounts describe "${build_sa}" \
    --project="${PROJECT_ID}" --format=json; then
  echo "Cleanup verification failed: at least one exact RevisionProof resource remains." >&2
  exit 5
fi

echo "Resource, custom IAM bindings, and project-scoped budget cleanup completed."
echo "Billing remains linked, enabled APIs remain enabled, and the project remains active."
echo "For complete isolation cleanup, separately review and run:"
echo "  gcloud projects delete ${PROJECT_ID}"
