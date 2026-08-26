#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
CONFIRM_PROJECT="${2:-}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

if [[ "${GCLOUD_ACCOUNT:-}" != "secureis@gmail.com" ]]; then
  echo "Refusing secret creation: unexpected gcloud account." >&2
  exit 2
fi
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
active_gcloud_account="$(gcloud config get-value account 2>/dev/null)"
if [[ "${active_gcloud_account}" != "${GCLOUD_ACCOUNT}" ]]; then
  echo "Refusing secret creation: active gcloud account is ${active_gcloud_account:-none}." >&2
  exit 2
fi

if [[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]; then
  echo "Pass the exact project id as argument 2: ${PROJECT_ID}" >&2
  exit 2
fi

writer_secret="${CLICKHOUSE_WRITER_SECRET:-revisionproof-clickhouse-writer-password}"
mcp_secret="${CLICKHOUSE_MCP_SECRET:-revisionproof-clickhouse-mcp-password}"
if [[ "${PROJECT_ID}" != revisionproof-* ]] \
  || [[ "${writer_secret}" != "revisionproof-clickhouse-writer-password" ]] \
  || [[ "${mcp_secret}" != "revisionproof-clickhouse-mcp-password" ]]; then
  echo "Refusing secret creation: project or secret name is outside RevisionProof." >&2
  exit 2
fi

actual_project_number="$(gcloud projects describe "${PROJECT_ID}" \
  --format='value(projectNumber)')"
project_labels="$(gcloud projects describe "${PROJECT_ID}" --format=json)"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]] \
  || ! jq -e '.labels.app == "revisionproof"
    and .labels.environment == "hackathon"
    and .labels["managed-by"] == "revisionproof-gcp"' \
    <<<"${project_labels}" >/dev/null; then
  echo "Refusing secret creation: project identity or labels do not match." >&2
  exit 3
fi

ensure_secret() {
  local secret_name="$1" existing_json status
  if existing_json="$(gcloud secrets describe "${secret_name}" \
    --project="${PROJECT_ID}" --format=json 2>&1)"; then
    if ! jq -e '.labels.app == "revisionproof"
      and .labels.environment == "hackathon"
      and .labels["managed-by"] == "revisionproof-gcp"' \
      <<<"${existing_json}" >/dev/null; then
      echo "Refusing to reuse unlabeled secret ${secret_name}." >&2
      exit 3
    fi
    return
  else
    status=$?
  fi
  if ! grep -Eqi 'NOT_FOUND|not found|does not exist' <<<"${existing_json}"; then
    printf '%s\n' "${existing_json}" >&2
    exit "${status}"
  fi
  gcloud secrets create "${secret_name}" \
    --project="${PROJECT_ID}" \
    --replication-policy=automatic \
    --labels="app=revisionproof,environment=hackathon,managed-by=revisionproof-gcp" >/dev/null
}

prompt_secret_value() {
  local prompt="$1" output_name="$2" first second
  read -r -s -p "${prompt}: " first
  printf '\n'
  read -r -s -p "Confirm ${prompt}: " second
  printf '\n'
  if [[ -z "${first}" || "${first}" != "${second}" ]]; then
    echo "Secret values were empty or did not match." >&2
    exit 4
  fi
  printf -v "${output_name}" '%s' "${first}"
  unset first second
}

ensure_secret "${writer_secret}"
ensure_secret "${mcp_secret}"
bash infra/gcp/setup-live-secret-access.sh "${ENV_FILE}"
writer_value=""
mcp_value=""
prompt_secret_value "RevisionProof writer password" writer_value
prompt_secret_value "RevisionProof MCP reader password" mcp_value
writer_version="$(printf '%s' "${writer_value}" | gcloud secrets versions add \
  "${writer_secret}" --project="${PROJECT_ID}" --data-file=- --format='value(name)')"
mcp_version="$(printf '%s' "${mcp_value}" | gcloud secrets versions add \
  "${mcp_secret}" --project="${PROJECT_ID}" --data-file=- --format='value(name)')"
unset writer_value mcp_value
echo "Created or versioned only the two labeled RevisionProof LIVE secrets."
echo "writer_secret_version=${writer_version##*/}"
echo "mcp_secret_version=${mcp_version##*/}"
