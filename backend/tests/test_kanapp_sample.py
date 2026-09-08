import hashlib
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from revisionproof.api import router
from revisionproof.assets import DEMO_ASSET_ID, KANAPP_ASSET_ID, require_demo_asset
from revisionproof.contracts import ApprovalRequest, CreateRunRequest, RunState
from revisionproof.editing.models import EditOperation, EditPlan
from revisionproof.main import app, settings

SAMPLE_SHA256 = "ce6270bbd3eac7359d173fa34386b8f00ab1bc83c571e0c9bb27e030003d4d91"
SAMPLE_URL = "/media/demo/kanapp_promo_english_editable_30s.mp4"


def test_catalog_defaults_to_exact_walkthrough_clip(service):
    api_app = FastAPI()
    api_app.state.service = service
    api_app.include_router(router)
    with TestClient(api_app) as client:
        response = client.get("/api/demo-assets")
    assert response.status_code == 200
    assets = response.json()
    assert [asset["asset_id"] for asset in assets] == [KANAPP_ASSET_ID, DEMO_ASSET_ID]
    assert assets[0]["source_url"] == SAMPLE_URL
    assert assets[0]["duration_seconds"] == 30
    assert (assets[0]["width"], assets[0]["height"]) == (1280, 720)
    _, path = require_demo_asset(KANAPP_ASSET_ID, service.settings.runtime_dir, service.executor)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SAMPLE_SHA256
    bundled = Path(__file__).resolve().parents[2] / "assets/demo" / path.name
    assert path.read_bytes() == bundled.read_bytes()
    _, legacy = require_demo_asset(DEMO_ASSET_ID, service.settings.runtime_dir, service.executor)
    assert legacy.name == "revisionproof_v1.mp4"
    assert legacy != path


def test_sample_media_serves_exact_bytes_and_supports_seeking(runtime_dir, monkeypatch):
    monkeypatch.setattr(settings, "runtime_dir", runtime_dir)
    with TestClient(app) as client:
        response = client.get(SAMPLE_URL)
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert hashlib.sha256(response.content).hexdigest() == SAMPLE_SHA256
        partial = client.get(SAMPLE_URL, headers={"Range": "bytes=0-1023"})
        assert partial.status_code == 206
        assert partial.content == response.content[:1024]
        assert client.get(SAMPLE_URL + ".bak").status_code == 404
        assert client.get("/media/demo/other.mp4").status_code == 404


@pytest.mark.asyncio
async def test_kanapp_plan_owns_correct_source_and_generates_preview(service):
    request = CreateRunRequest(
        asset_id=KANAPP_ASSET_ID,
        feedback="Zoom in from 4 to 8 seconds",
        edit_plan=EditPlan(
            source_duration=30,
            operations=[EditOperation(kind="zoom", start=4, end=8)],
        ),
    )
    snapshot = await service.create_run(request)
    assert snapshot.asset.asset_id == KANAPP_ASSET_ID
    assert snapshot.asset.source_url == SAMPLE_URL
    owned = service.settings.runtime_dir / "runs" / snapshot.run_id / "source/source.mp4"
    assert hashlib.sha256(owned.read_bytes()).hexdigest() == SAMPLE_SHA256
    assert not any(e.source == "fixture.segment_index" for e in snapshot.evidence)
    preview = service.generate_previews(snapshot.run_id)
    assert preview.state is RunState.PREVIEWS_READY
    assert preview.candidates
    service.approve(snapshot.run_id, ApprovalRequest(candidate_id="A"))
    service.render_approved_version(snapshot.run_id)
    assert snapshot.state is RunState.READY, snapshot.proof
    assert snapshot.proof.publish_allowed


@pytest.mark.asyncio
async def test_kanapp_cannot_use_legacy_scene_index(service):
    with pytest.raises(ValueError, match="requires an edit plan"):
        await service.create_run(
            CreateRunRequest(asset_id=KANAPP_ASSET_ID, feedback="Make the reveal more intentional")
        )
    with pytest.raises(ValueError, match="allowlist"):
        require_demo_asset("../../other", service.settings.runtime_dir, service.executor)
