#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${1:-infra/gcp/foundation.env}"
LIVE_ENV_FILE="${2:-infra/gcp/live.env}"
CONFIRM_PROJECT="${3:-}"
if [[ ! -f "${ENV_FILE}" || ! -f "${LIVE_ENV_FILE}" ]]; then
  echo "Missing foundation or verified LIVE state file." >&2
  exit 2
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"
foundation_clickhouse_host="${CLICKHOUSE_HOST:-}"
# shellcheck source=/dev/null
source "${LIVE_ENV_FILE}"

if [[ "${GCLOUD_ACCOUNT:-}" != "secureis@gmail.com" ]] \
  || [[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]; then
  echo "Refusing LIVE deploy: account or project confirmation does not match." >&2
  exit 2
fi
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
active_gcloud_account="$(gcloud config get-value account 2>/dev/null)"
if [[ "${active_gcloud_account}" != "${GCLOUD_ACCOUNT}" ]]; then
  echo "Refusing LIVE deploy: active gcloud account is ${active_gcloud_account:-none}." >&2
  exit 2
fi
if [[ "${CLICKHOUSE_HOST}" != "${foundation_clickhouse_host}" ]] \
  || [[ ! "${CLICKHOUSE_HOST}" =~ ^[a-z0-9][a-z0-9.-]*\.clickhouse\.cloud$ ]] \
  || [[ ! "${CLICKHOUSE_WRITER_SECRET_VERSION}" =~ ^[1-9][0-9]*$ ]] \
  || [[ ! "${CLICKHOUSE_MCP_SECRET_VERSION}" =~ ^[1-9][0-9]*$ ]]; then
  echo "Refusing LIVE deploy: verified host or numeric secret versions do not match." >&2
  exit 3
fi
actual_project_number="$(gcloud projects describe "${PROJECT_ID}" \
  --format='value(projectNumber)')"
managed_label="$(gcloud projects describe "${PROJECT_ID}" \
  --format='value(labels.managed-by)')"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]] \
  || [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing LIVE deploy: project identity or label does not match." >&2
  exit 3
fi

gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=cloudbuild.yaml \
  --gcs-source-staging-dir="gs://${GCS_BUCKET}/cloud-build-source" \
  --substitutions="_CONFIRM_LIVE=YES,_REGION=${REGION},_SERVICE=${SERVICE_NAME},_REPOSITORY=${ARTIFACT_REPOSITORY},_GCS_BUCKET=${GCS_BUCKET},_CLICKHOUSE_HOST=${CLICKHOUSE_HOST},_VERTEX_LOCATION=global,_GEMINI_MODEL=gemini-3.5-flash-lite,_WRITER_SECRET_VERSION=${CLICKHOUSE_WRITER_SECRET_VERSION},_MCP_SECRET_VERSION=${CLICKHOUSE_MCP_SECRET_VERSION}" \
  .

gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" --region="${REGION}" \
  --format='yaml(metadata.name,metadata.labels,status.url,status.latestReadyRevisionName,spec.template.spec.containers[0].env)'
