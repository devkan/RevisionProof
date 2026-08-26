from fastapi.testclient import TestClient

from revisionproof.contracts import ExecutionMode
from revisionproof.main import app, settings
from revisionproof.settings import Settings


def test_vertex_defaults_match_credential_verified_global_models(monkeypatch) -> None:
    monkeypatch.delenv("REVISIONPROOF_GEMINI_MODEL", raising=False)
    monkeypatch.delenv("REVISIONPROOF_GOOGLE_CLOUD_LOCATION", raising=False)
    defaults = Settings(_env_file=None)

    assert defaults.gemini_model == "gemini-3.5-flash-lite"
    assert defaults.google_cloud_location == "global"


def test_operational_routes_use_cloud_run_safe_paths() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        ready = client.get("/ready")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_legacy_operational_routes_remain_local_compatibility_aliases() -> None:
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200


def test_ready_fails_closed_when_live_configuration_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mode", ExecutionMode.LIVE)
    monkeypatch.setattr(settings, "google_cloud_project", None)
    monkeypatch.setattr(settings, "gcs_bucket", None)
    monkeypatch.setattr(settings, "clickhouse_host", None)
    monkeypatch.setattr(settings, "clickhouse_writer_password", None)
    monkeypatch.setattr(settings, "clickhouse_mcp_password", None)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert set(response.json()["missing"]) == {
        "google_cloud_project",
        "gcs_bucket",
        "clickhouse_host",
        "clickhouse_writer_password",
        "clickhouse_mcp_password",
    }
