#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

writer_secret="${CLICKHOUSE_WRITER_SECRET:-revisionproof-clickhouse-writer-password}"
mcp_secret="${CLICKHOUSE_MCP_SECRET:-revisionproof-clickhouse-mcp-password}"
runtime_sa="${RUNTIME_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

actual_project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
managed_label="$(gcloud projects describe "${PROJECT_ID}" --format='value(labels.managed-by)')"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]] \
  || [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing secret IAM: project identity or managed label does not match." >&2
  exit 3
fi
if [[ "${writer_secret}" != "revisionproof-clickhouse-writer-password" ]] \
  || [[ "${mcp_secret}" != "revisionproof-clickhouse-mcp-password" ]]; then
  echo "Refusing secret IAM: unexpected RevisionProof secret name." >&2
  exit 3
fi

for secret_name in "${writer_secret}" "${mcp_secret}"; do
  secret_json="$(gcloud secrets describe "${secret_name}" \
    --project="${PROJECT_ID}" --format=json)"
  if ! jq -e '.labels.app == "revisionproof"
    and .labels.environment == "hackathon"
    and .labels["managed-by"] == "revisionproof-gcp"' \
    <<<"${secret_json}" >/dev/null; then
    echo "Refusing secret IAM: ${secret_name} lacks exact RevisionProof labels." >&2
    exit 3
  fi
  gcloud secrets add-iam-policy-binding "${secret_name}" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${runtime_sa}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null
done

echo "LIVE secret access is scoped to the two exact RevisionProof secrets."
echo "runtime_service_account=${runtime_sa}"
echo "writer_secret=${writer_secret}"
echo "mcp_secret=${mcp_secret}"
