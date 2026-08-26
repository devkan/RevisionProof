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
  PROJECT_ID PROJECT_NAME GCLOUD_ACCOUNT EXPECTED_PROJECT_NUMBER ADOPT_EXISTING_PROJECT
  BILLING_ACCOUNT_ID REGION ARTIFACT_REPOSITORY
  SERVICE_NAME RUNTIME_SERVICE_ACCOUNT BUILD_SERVICE_ACCOUNT GCS_BUCKET
  MIN_INSTANCES BUDGET_AMOUNT_UNITS BUDGET_CURRENCY_CODE BUDGET_DISPLAY_NAME
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" || "${!name}" == REPLACE_* ]]; then
    echo "Required variable ${name} is not configured." >&2
    exit 2
  fi
done

if [[ "${GCLOUD_ACCOUNT}" != "secureis@gmail.com" ]]; then
  echo "GCLOUD_ACCOUNT must be the locked RevisionProof owner secureis@gmail.com." >&2
  exit 2
fi
export CLOUDSDK_CORE_ACCOUNT="${GCLOUD_ACCOUNT}"
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"

if [[ ! "${PROJECT_ID}" =~ ^revisionproof-[a-z0-9-]{6,16}$ ]]; then
  echo "PROJECT_ID must be a dedicated lowercase revisionproof-* id of at most 30 characters." >&2
  exit 2
fi
if [[ "${GCS_BUCKET}" != "${PROJECT_ID}-media" ]]; then
  echo "GCS_BUCKET must be ${PROJECT_ID}-media so cleanup cannot target an unrelated bucket." >&2
  exit 2
fi
if [[ "${RUNTIME_SERVICE_ACCOUNT}" != "revisionproof-runtime" ]] \
  || [[ "${BUILD_SERVICE_ACCOUNT}" != "revisionproof-build" ]]; then
  echo "Service-account names must be revisionproof-runtime and revisionproof-build." >&2
  exit 2
fi
if [[ ! "${MIN_INSTANCES}" =~ ^[01]$ ]]; then
  echo "MIN_INSTANCES must be 0 or 1 because the service is capped at one instance." >&2
  exit 2
fi
if [[ ! "${BUDGET_AMOUNT_UNITS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BUDGET_AMOUNT_UNITS must be a positive whole-unit alert amount." >&2
  exit 2
fi
if [[ ! "${BUDGET_CURRENCY_CODE}" =~ ^[A-Z]{3}$ ]]; then
  echo "BUDGET_CURRENCY_CODE must be the billing account's three-letter currency code." >&2
  exit 2
fi
if [[ ! "${EXPECTED_PROJECT_NUMBER}" =~ ^[0-9]+$ ]]; then
  echo "EXPECTED_PROJECT_NUMBER must be the exact numeric project number recorded after creation." >&2
  exit 2
fi
if [[ ! "${ADOPT_EXISTING_PROJECT}" =~ ^(YES|NO)$ ]]; then
  echo "ADOPT_EXISTING_PROJECT must be YES or NO." >&2
  exit 2
fi

command -v gcloud >/dev/null
command -v jq >/dev/null

managed_label="revisionproof-gcp"
if gcloud projects describe "${PROJECT_ID}" >/dev/null 2>&1; then
  existing_project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
  if [[ "${existing_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]]; then
    echo "Refusing to modify ${PROJECT_ID}: expected project number ${EXPECTED_PROJECT_NUMBER}, got ${existing_project_number}." >&2
    exit 3
  fi
  existing_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
  if [[ -n "${existing_label}" && "${existing_label}" != "${managed_label}" ]]; then
    echo "Refusing to modify existing project ${PROJECT_ID}: managed-by label is ${existing_label}." >&2
    exit 3
  fi
  if [[ -z "${existing_label}" ]]; then
    if [[ "${ADOPT_EXISTING_PROJECT}" != "YES" ]]; then
      echo "Refusing to adopt unlabeled project ${PROJECT_ID}; set ADOPT_EXISTING_PROJECT=YES after verifying its project number and billing link." >&2
      exit 3
    fi
    gcloud alpha projects update "${PROJECT_ID}" \
      --update-labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}"
  fi
  if ! gcloud projects describe "${PROJECT_ID}" --format=json \
    | jq -e --arg managed_label "${managed_label}" \
      '.labels.app == "revisionproof"
        and .labels.environment == "hackathon"
        and .labels["managed-by"] == $managed_label' >/dev/null; then
    gcloud alpha projects update "${PROJECT_ID}" \
      --update-labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}"
  fi
else
  echo "Project ${PROJECT_ID} does not exist. Create it first, record its project number, then rerun this script." >&2
  exit 3
fi

expected_billing="billingAccounts/${BILLING_ACCOUNT_ID}"
current_billing="$(gcloud billing projects describe "${PROJECT_ID}" \
  --format='value(billingAccountName)')"
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
cloud_run_deployer_role_id="revisionproofCloudRunDeployer"
cloud_run_deployer_role="projects/${PROJECT_ID}/roles/${cloud_run_deployer_role_id}"
cloud_run_deployer_permissions="resourcemanager.projects.get,run.configurations.get,run.configurations.list,run.locations.get,run.locations.list,run.operations.get,run.revisions.get,run.revisions.list,run.routes.get,run.routes.list,run.services.create,run.services.get,run.services.getIamPolicy,run.services.list,run.services.setIamPolicy,run.services.update"

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

if gcloud iam roles describe "${cloud_run_deployer_role_id}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam roles update "${cloud_run_deployer_role_id}" \
    --project="${PROJECT_ID}" \
    --title="RevisionProof Cloud Run deployer" \
    --description="Create or update only Cloud Run services and their public-access policy." \
    --permissions="${cloud_run_deployer_permissions}" \
    --stage=GA >/dev/null
else
  gcloud iam roles create "${cloud_run_deployer_role_id}" \
    --project="${PROJECT_ID}" \
    --title="RevisionProof Cloud Run deployer" \
    --description="Create or update only Cloud Run services and their public-access policy." \
    --permissions="${cloud_run_deployer_permissions}" \
    --stage=GA >/dev/null
fi

for role in roles/aiplatform.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${runtime_sa}" \
    --role="${role}" \
    --condition=None >/dev/null
done
for role in roles/logging.logWriter "${cloud_run_deployer_role}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${build_sa}" \
    --role="${role}" \
    --condition=None >/dev/null
done
build_project_policy="$(gcloud projects get-iam-policy "${PROJECT_ID}" --format=json)"
if jq -e --arg member "serviceAccount:${build_sa}" \
  'any(.bindings[]?; .role == "roles/run.admin"
    and any(.members[]?; . == $member))' <<<"${build_project_policy}" >/dev/null; then
  gcloud projects remove-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${build_sa}" \
    --role="roles/run.admin" --condition=None --quiet >/dev/null
fi
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
else
  repository_json="$(gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
    --location="${REGION}" --project="${PROJECT_ID}" --format=json)"
  expected_repository="projects/${PROJECT_ID}/locations/${REGION}/repositories/${ARTIFACT_REPOSITORY}"
  if ! jq -e --arg expected "${expected_repository}" \
    '.name == $expected and .format == "DOCKER"' <<<"${repository_json}" >/dev/null; then
    echo "Refusing repository drift: expected Docker repository ${expected_repository}." >&2
    exit 3
  fi
  if ! jq -e --arg managed_label "${managed_label}" \
    '.labels.app == "revisionproof"
      and .labels.environment == "hackathon"
      and .labels["managed-by"] == $managed_label' <<<"${repository_json}" >/dev/null; then
    gcloud artifacts repositories update "${ARTIFACT_REPOSITORY}" \
      --location="${REGION}" \
      --update-labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}" \
      --project="${PROJECT_ID}"
  fi
fi

gcloud artifacts repositories add-iam-policy-binding "${ARTIFACT_REPOSITORY}" \
  --location="${REGION}" \
  --member="serviceAccount:${build_sa}" \
  --role="roles/artifactregistry.writer" \
  --project="${PROJECT_ID}" >/dev/null

if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${GCS_BUCKET}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention \
    --soft-delete-duration=0
fi
bucket_json="$(gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=json)"
bucket_owner_match="$(gcloud storage buckets list \
  --project="${PROJECT_ID}" \
  --filter="name=${GCS_BUCKET}" \
  --format='value(name)')"
if [[ "${bucket_owner_match}" != "${GCS_BUCKET}" ]]; then
  echo "Refusing bucket drift: gs://${GCS_BUCKET} is not owned by ${PROJECT_ID}." >&2
  exit 3
fi
bucket_location="$(jq -r '.location // empty | ascii_downcase' <<<"${bucket_json}")"
if [[ "${bucket_location}" != "${REGION}" ]]; then
  echo "Refusing bucket drift: expected ${REGION}, got ${bucket_location:-unknown}." >&2
  exit 3
fi
if ! jq -e '.uniform_bucket_level_access == true' <<<"${bucket_json}" >/dev/null; then
  gcloud storage buckets update "gs://${GCS_BUCKET}" --uniform-bucket-level-access
fi
if ! jq -e '.public_access_prevention == "enforced"' <<<"${bucket_json}" >/dev/null; then
  gcloud storage buckets update "gs://${GCS_BUCKET}" --public-access-prevention
fi
gcloud storage buckets update "gs://${GCS_BUCKET}" \
  --lifecycle-file="infra/gcp/media-lifecycle.json"
gcloud storage buckets update "gs://${GCS_BUCKET}" \
  --clear-soft-delete

if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" --format=json \
  | jq -e --arg managed_label "${managed_label}" \
    '.labels.app == "revisionproof"
      and .labels.environment == "hackathon"
      and .labels["managed-by"] == $managed_label' >/dev/null; then
  gcloud storage buckets update "gs://${GCS_BUCKET}" \
    --update-labels="app=revisionproof,environment=hackathon,managed-by=${managed_label}"
fi
gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
  --member="serviceAccount:${runtime_sa}" \
  --role="roles/storage.objectCreator" >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
  --member="serviceAccount:${runtime_sa}" \
  --role="roles/storage.objectViewer" >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
  --member="serviceAccount:${build_sa}" \
  --role="roles/storage.objectViewer" >/dev/null

remove_project_binding_if_present() {
  local member="$1" role="$2" policy
  policy="$(gcloud projects get-iam-policy "${PROJECT_ID}" --format=json)"
  if jq -e --arg member "${member}" --arg role "${role}" \
    'any(.bindings[]?; .role == $role and any(.members[]?; . == $member))' \
    <<<"${policy}" >/dev/null; then
    gcloud projects remove-iam-policy-binding "${PROJECT_ID}" \
      --member="${member}" --role="${role}" --condition=None --quiet >/dev/null
  fi
}

# Converge older foundation runs from project-wide access to exact resource bindings.
remove_project_binding_if_present \
  "serviceAccount:${build_sa}" "roles/artifactregistry.writer"
remove_project_binding_if_present \
  "serviceAccount:${build_sa}" "roles/storage.objectViewer"

bucket_policy="$(gcloud storage buckets get-iam-policy "gs://${GCS_BUCKET}" --format=json)"
if jq -e --arg member "serviceAccount:${runtime_sa}" \
  'any(.bindings[]?; .role == "roles/storage.objectAdmin"
    and any(.members[]?; . == $member))' <<<"${bucket_policy}" >/dev/null; then
  gcloud storage buckets remove-iam-policy-binding "gs://${GCS_BUCKET}" \
    --member="serviceAccount:${runtime_sa}" \
    --role="roles/storage.objectAdmin" >/dev/null
fi

budget_name="$(gcloud billing budgets list \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
  --format='value(name)' \
  --limit=1)"
if [[ -z "${budget_name}" ]]; then
  budget_name="$(gcloud billing budgets create \
    --billing-account="${BILLING_ACCOUNT_ID}" \
    --display-name="${BUDGET_DISPLAY_NAME}" \
    --budget-amount="${BUDGET_AMOUNT_UNITS}${BUDGET_CURRENCY_CODE}" \
    --filter-projects="projects/${project_number}" \
    --threshold-rule=percent=0.50 \
    --threshold-rule=percent=0.90 \
    --threshold-rule=percent=1.00 \
    --format='value(name)')"
else
  budget_json="$(gcloud billing budgets list \
    --billing-account="${BILLING_ACCOUNT_ID}" \
    --filter="displayName='${BUDGET_DISPLAY_NAME}'" \
    --format=json \
    --limit=1)"
  if ! jq -e \
    --arg units "${BUDGET_AMOUNT_UNITS}" \
    --arg currency "${BUDGET_CURRENCY_CODE}" \
    --arg project "projects/${project_number}" \
    '.[0].amount.specifiedAmount.currencyCode == $currency
      and (.[0].amount.specifiedAmount.units | tostring) == $units
      and .[0].budgetFilter.projects == [$project]
      and ([.[0].thresholdRules[].thresholdPercent] | sort) == [0.5, 0.9, 1]' \
    <<<"${budget_json}" >/dev/null; then
    echo "Refusing budget drift: ${BUDGET_DISPLAY_NAME} does not match the locked amount, project, currency, and thresholds." >&2
    exit 3
  fi
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
echo "budget=${budget_name} (${BUDGET_AMOUNT_UNITS} ${BUDGET_CURRENCY_CODE} alerts; not a hard cap)"
echo "Next: run infra/gcp/inventory.sh, then submit cloudbuild.foundation.yaml."
