from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GCP_SCRIPTS = sorted((PROJECT_ROOT / "infra" / "gcp").glob("*.sh"))


@pytest.mark.parametrize("script_path", GCP_SCRIPTS, ids=lambda path: path.name)
def test_every_gcp_script_pins_the_locked_account_and_project(
    script_path: Path,
) -> None:
    source = script_path.read_text(encoding="utf-8")

    assert "secureis@gmail.com" in source
    assert 'export CLOUDSDK_CORE_ACCOUNT="${GCLOUD_ACCOUNT}"' in source
    assert 'export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"' in source


def test_cleanup_requires_exact_identity_labels_and_execute_flag() -> None:
    source = (PROJECT_ROOT / "infra" / "gcp" / "cleanup.sh").read_text(encoding="utf-8")

    assert '[[ "${CONFIRM_PROJECT}" != "${PROJECT_ID}" ]]' in source
    assert '[[ "${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}" ]]' in source
    assert '[[ "${managed_label}" != "revisionproof-gcp" ]]' in source
    assert '[[ "${MODE}" != "--execute" ]]' in source
    assert '[[ "${GCS_BUCKET}" != "${PROJECT_ID}-media" ]]' in source


@pytest.mark.parametrize(
    "script_name",
    ["bootstrap-live.sh", "create-live-secrets.sh", "deploy-live.sh"],
)
def test_live_mutation_scripts_require_exact_project_confirmation(
    script_name: str,
) -> None:
    source = (PROJECT_ROOT / "infra" / "gcp" / script_name).read_text(encoding="utf-8")

    assert '"${CONFIRM_PROJECT}" != "${PROJECT_ID}"' in source
    assert '"${actual_project_number}" != "${EXPECTED_PROJECT_NUMBER}"' in source
