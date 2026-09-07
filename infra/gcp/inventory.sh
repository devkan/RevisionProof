#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

if [[ "${GCLOUD_ACCOUNT:-}" != "secureis@gmail.com" ]]; then
  echo "Refusing inventory: unexpected gcloud account." >&2
  exit 2
fi
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
active_gcloud_account="$(gcloud config get-value account 2>/dev/null)"
if [[ "${active_gcloud_account}" != "${GCLOUD_ACCOUNT}" ]]; then
  echo "Refusing inventory: active gcloud account is ${active_gcloud_account:-none}." >&2
  exit 2
fi

actual_project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]]; then
  echo "Refusing inventory: expected project ${EXPECTED_PROJECT_NUMBER}, got ${actual_project_number}." >&2
  exit 3
fi
managed_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
if [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing inventory: ${PROJECT_ID} is not managed-by=revisionproof-gcp." >&2
  exit 3
fi

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
  --filter="email:(${RUNTIME_SERVICE_ACCOUNT} OR ${BUILD_SERVICE_ACCOUNT})" \
  --format='yaml(email,displayName,disabled,uniqueId)'
echo "=== project IAM for RevisionProof service accounts ==="
gcloud projects get-iam-policy "${PROJECT_ID}" \
  --flatten='bindings[].members' \
  --filter="bindings.members:(serviceAccount:${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com OR serviceAccount:${BUILD_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com)" \
  --format='yaml(bindings.role,bindings.members,bindings.condition)'
echo "=== RevisionProof custom Cloud Run deployer role ==="
gcloud iam roles describe revisionproofCloudRunDeployer \
  --project="${PROJECT_ID}" \
  --format='yaml(name,title,description,includedPermissions,stage,deleted)'
echo "=== runtime service-account policy ==="
gcloud iam service-accounts get-iam-policy \
  "${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" --format=yaml
echo "=== artifact repository ==="
gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" --project="${PROJECT_ID}" --format=yaml
echo "=== container images and digests ==="
gcloud artifacts docker images list \
  "${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPOSITORY}" \
  --include-tags --project="${PROJECT_ID}" \
  --format='yaml(package,version,tags,createTime,updateTime,imageSizeBytes)'
echo "=== media bucket ==="
gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=yaml
echo "=== media bucket IAM ==="
gcloud storage buckets get-iam-policy "gs://${GCS_BUCKET}" --format=yaml
echo "=== media and lifecycle-managed build-source objects ==="
list_objects() {
  local bucket_pattern="$1" output status
  if output="$(gcloud storage ls --long --recursive "${bucket_pattern}" 2>&1)"; then
    [[ -n "${output}" ]] && printf '%s\n' "${output}" || echo "none"
    return
  else
    status=$?
  fi
  if grep -Eqi 'matched no objects|no URLs matched|not contain any objects' <<<"${output}"; then
    echo "none"
    return
  fi
  printf '%s\n' "${output}" >&2
  exit "${status}"
}
list_objects "gs://${GCS_BUCKET}/**"
echo "=== Cloud Build history ==="
gcloud builds list --project="${PROJECT_ID}" --limit=20 \
  --format='yaml(id,status,createTime,startTime,finishTime,source,images,results.images,substitutions,serviceAccount)'
echo "=== legacy default Cloud Build source bucket ==="
default_build_bucket="${PROJECT_ID}_cloudbuild"
if build_bucket_yaml="$(gcloud storage buckets describe "gs://${default_build_bucket}" --format=yaml 2>&1)"; then
  printf '%s\n' "${build_bucket_yaml}"
  list_objects "gs://${default_build_bucket}/**"
elif grep -Eqi 'NOT_FOUND|not found|does not exist' <<<"${build_bucket_yaml}"; then
  echo "absent"
else
  printf '%s\n' "${build_bucket_yaml}" >&2
  exit 4
fi
echo "=== Cloud Run service ==="
if run_yaml="$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" --project="${PROJECT_ID}" --format=yaml 2>&1)"; then
  printf '%s\n' "${run_yaml}"
elif grep -Eqi 'NOT_FOUND|not found|does not exist' <<<"${run_yaml}"; then
  echo "not deployed"
else
  printf '%s\n' "${run_yaml}" >&2
  exit 4
fi
echo "=== RevisionProof-managed secrets (may be absent before LIVE) ==="
gcloud secrets list --project="${PROJECT_ID}" \
  --filter="labels.managed-by=revisionproof-gcp" \
  --format='yaml(name,createTime,labels,replication)'
for secret_name in \
  "${CLICKHOUSE_WRITER_SECRET:-revisionproof-clickhouse-writer-password}" \
  "${CLICKHOUSE_MCP_SECRET:-revisionproof-clickhouse-mcp-password}"; do
  if gcloud secrets describe "${secret_name}" \
    --project="${PROJECT_ID}" --format='value(name)' >/dev/null 2>&1; then
    echo "--- IAM ${secret_name} ---"
    gcloud secrets get-iam-policy "${secret_name}" \
      --project="${PROJECT_ID}" --format=yaml
    echo "--- enabled versions ${secret_name} ---"
    gcloud secrets versions list "${secret_name}" \
      --project="${PROJECT_ID}" --filter='state=enabled' \
      --format='yaml(name,state,createTime,destroyTime)'
  fi
done
