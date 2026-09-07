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

if [[ "${GCLOUD_ACCOUNT:-}" != "secureis@gmail.com" ]] \
  || [[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]; then
  echo "Refusing LIVE bootstrap: account or project confirmation does not match." >&2
  exit 2
fi
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
active_gcloud_account="$(gcloud config get-value account 2>/dev/null)"
if [[ "${active_gcloud_account}" != "${GCLOUD_ACCOUNT}" ]]; then
  echo "Refusing LIVE bootstrap: active gcloud account is ${active_gcloud_account:-none}." >&2
  exit 2
fi

if [[ ! "${CLICKHOUSE_HOST:-}" =~ ^[a-z0-9][a-z0-9.-]*\.clickhouse\.cloud$ ]]; then
  echo "Refusing LIVE bootstrap: invalid ClickHouse Cloud host." >&2
  exit 2
fi
actual_project_number="$(gcloud projects describe "${PROJECT_ID}" \
  --format='value(projectNumber)')"
managed_label="$(gcloud projects describe "${PROJECT_ID}" \
  --format='value(labels.managed-by)')"
if [[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]] \
  || [[ "${managed_label}" != "revisionproof-gcp" ]]; then
  echo "Refusing LIVE bootstrap: project identity or label does not match." >&2
  exit 3
fi

writer_secret="${CLICKHOUSE_WRITER_SECRET:-revisionproof-clickhouse-writer-password}"
mcp_secret="${CLICKHOUSE_MCP_SECRET:-revisionproof-clickhouse-mcp-password}"
latest_enabled_version() {
  local raw_version
  raw_version="$(gcloud secrets versions list "$1" --project="${PROJECT_ID}" \
    --filter='state=enabled' --sort-by='~createTime' --limit=1 --format='value(name)')"
  printf '%s' "${raw_version##*/}"
}
writer_version="$(latest_enabled_version "${writer_secret}")"
mcp_version="$(latest_enabled_version "${mcp_secret}")"
if [[ ! "${writer_version}" =~ ^[1-9][0-9]*$ ]] \
  || [[ ! "${mcp_version}" =~ ^[1-9][0-9]*$ ]]; then
  echo "Refusing LIVE bootstrap: enabled numeric secret versions are required." >&2
  exit 3
fi

export REVISIONPROOF_MODE="LIVE"
export REVISIONPROOF_GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export REVISIONPROOF_GOOGLE_CLOUD_LOCATION="global"
export REVISIONPROOF_GEMINI_MODEL="gemini-3.5-flash-lite"
export REVISIONPROOF_EMBEDDING_MODEL="text-embedding-005"
export REVISIONPROOF_GCS_BUCKET="${GCS_BUCKET}"
export REVISIONPROOF_CLICKHOUSE_HOST="${CLICKHOUSE_HOST}"
export REVISIONPROOF_CLICKHOUSE_PORT="8443"
export REVISIONPROOF_CLICKHOUSE_SECURE="true"
export REVISIONPROOF_CLICKHOUSE_VERIFY="true"
REVISIONPROOF_CLICKHOUSE_WRITER_PASSWORD="$(gcloud secrets versions access \
  "${writer_version}" --secret="${writer_secret}" --project="${PROJECT_ID}")"
REVISIONPROOF_CLICKHOUSE_MCP_PASSWORD="$(gcloud secrets versions access \
  "${mcp_version}" --secret="${mcp_secret}" --project="${PROJECT_ID}")"
export REVISIONPROOF_CLICKHOUSE_WRITER_PASSWORD
export REVISIONPROOF_CLICKHOUSE_MCP_PASSWORD
trap 'unset REVISIONPROOF_CLICKHOUSE_WRITER_PASSWORD REVISIONPROOF_CLICKHOUSE_MCP_PASSWORD' EXIT

python_bin="${REVISIONPROOF_PYTHON_BIN:-backend/.venv/bin/python}"
if [[ ! -x "${python_bin}" && -x backend/.venv/Scripts/python.exe ]]; then
  python_bin="backend/.venv/Scripts/python.exe"
fi
if [[ ! -x "${python_bin}" ]]; then
  echo "Missing backend live Python environment." >&2
  exit 3
fi
if [[ ! -f runtime/demo/revisionproof_v1.mp4 ]]; then
  "${python_bin}" scripts/generate_demo_assets.py --demo-only
fi
"${python_bin}" scripts/bootstrap_live.py

umask 077
live_env="infra/gcp/live.env"
live_env_tmp="${live_env}.tmp"
printf 'export CLICKHOUSE_HOST="%s"\n' "${CLICKHOUSE_HOST}" >"${live_env_tmp}"
printf 'export CLICKHOUSE_WRITER_SECRET_VERSION="%s"\n' "${writer_version}" >>"${live_env_tmp}"
printf 'export CLICKHOUSE_MCP_SECRET_VERSION="%s"\n' "${mcp_version}" >>"${live_env_tmp}"
mv "${live_env_tmp}" "${live_env}"
echo "LIVE bootstrap passed; pinned non-secret deployment state in ${live_env}."
