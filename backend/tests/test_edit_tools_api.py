from __future__ import annotations

import hashlib
import io

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from revisionproof.api import router
from revisionproof.contracts import ExecutionMode
from revisionproof.media.upload_limit import UploadBodyLimit
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings


def client_for(tmp_path):
    settings = Settings(_env_file=None, mode=ExecutionMode.FIXTURE, runtime_dir=tmp_path)
    app = FastAPI()
    app.state.service = RevisionProofService(settings, InMemoryRunRepository())
    app.add_middleware(
        UploadBodyLimit,
        max_file_bytes=settings.max_upload_bytes,
        max_logo_bytes=settings.max_logo_bytes,
    )
    app.include_router(router)
    return TestClient(app)


def png_bytes() -> bytes:
    image = Image.new("RGBA", (120, 60), (20, 220, 240, 255))
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


def test_logo_upload_returns_frozen_asset_and_rejects_checksum_mismatch(tmp_path):
    client = client_for(tmp_path)
    content = png_bytes()
    response = client.post(
        "/api/edit-assets/logo",
        files={"file": ("kanapp.png", content, "image/png")},
        headers={"X-Content-SHA256": hashlib.sha256(content).hexdigest()},
    )
    assert response.status_code == 201, response.text
    asset = response.json()
    assert asset["preview_url"].endswith(f"/{asset['asset_id']}.png")
    assert (tmp_path / "edit-assets" / f"{asset['asset_id']}.png").is_file()
    rejected = client.post(
        "/api/edit-assets/logo",
        files={"file": ("kanapp.png", content, "image/png")},
        headers={"X-Content-SHA256": "0" * 64},
    )
    assert rejected.status_code == 422
    assert "incomplete" in rejected.json()["detail"]


def test_transcription_fails_truthfully_outside_live_mode(tmp_path):
    client = client_for(tmp_path)
    response = client.post(
        "/api/transcriptions",
        data={"language": "mixed", "asset_id": "01M00000000000000000000000"},
    )
    assert response.status_code == 409
    assert "LIVE Google Gemini" in response.json()["detail"]


def test_fixture_scene_search_is_opt_in_and_selected_result_anchors_plan(runtime_dir):
    client = client_for(runtime_dir)
    searched = client.post(
        "/api/scene-search",
        data={"query": "the product dashboard", "asset_id": "01M00000000000000000000000"},
    )
    assert searched.status_code == 200, searched.text
    result = searched.json()
    assert result["source"] == "fixture.scene_search"
    assert result["matches"]
    hit = result["matches"][0]
    plan = {
        "source_duration": 30,
        "operations": [
            {
                "kind": "zoom",
                "start": hit["start_seconds"],
                "end": hit["end_seconds"],
                "text": "",
                "position": "bottom",
                "threshold_db": -40,
                "min_silence": 0.7,
                "detected": False,
                "rate": 1,
                "volume_db": 0,
                "asset_id": "",
                "asset_sha256": "",
            }
        ],
    }
    created = client.post(
        "/api/runs",
        json={
            "asset_id": "01M00000000000000000000000",
            "feedback": "Zoom the dashboard scene",
            "edit_plan": plan,
            "scene_search_id": result["search_id"],
            "scene_segment_id": hit["segment_id"],
        },
        headers={"Idempotency-Key": "smart-scene-test"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["evidence"][0]["segment_id"] == hit["segment_id"]
    assert created.json()["evidence"][0]["source"] == "fixture.segment_index"
