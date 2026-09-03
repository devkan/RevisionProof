from __future__ import annotations

import hashlib
import io
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from revisionproof.api import router
from revisionproof.contracts import ApprovalRequest, ExecutionMode, TimeRange
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import MediaInfo
from revisionproof.media.source import (
    SourceUploadError,
    copy_source,
    interpret_selected_range,
    validate_source,
)
from revisionproof.media.upload_limit import UploadBodyLimit
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings


@pytest.fixture(scope="module")
def uploaded_clips(tmp_path_factory):
    folder = tmp_path_factory.mktemp("different-source")
    executor = MediaExecutor(90)
    clips = []
    for name, size, rate, duration, audio in (
        ("portrait", "360x640", 30, 12, True),
        ("silent", "640x360", 24, 4, False),
        ("fractional-short", "320x180", 30, 4.01, True),
        ("fractional-long", "320x180", 30, 6.01, True),
        ("fractional-control", "320x180", 30, 4.04, True),
    ):
        clip = folder / f"{name}.mp4"
        args = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={size}:rate={rate}",
        ]
        if audio:
            args += ["-f", "lavfi", "-i", "sine=frequency=660:sample_rate=48000"]
        args += [
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
        ]
        if audio:
            args += ["-c:a", "aac"]
        args += [str(clip)]
        executor.run(args, expected_output=clip)
        clips.append(clip)
    return clips


def app_client(tmp_path):
    settings = Settings(
        _env_file=None, mode=ExecutionMode.FIXTURE, runtime_dir=tmp_path, intelligence_enabled=True
    )
    service = RevisionProofService(settings, InMemoryRunRepository())
    service.fixture_locator.locate = Mock(side_effect=AssertionError("Never use demo anchors"))
    app = FastAPI()
    app.state.service = service
    app.add_middleware(UploadBodyLimit, max_file_bytes=settings.max_upload_bytes)
    app.include_router(router)
    return TestClient(app), service


@pytest.mark.parametrize(
    "clip_index,start,end,duration",
    [(0, 2, 8, 12), (1, 0, 4, 4), (2, 0, 4, 4.01), (3, 0, 4, 6.01), (4, 0, 4, 4.04)],
)
def test_upload_to_full_video_uses_selected_source_and_preserves_timing(
    tmp_path,
    uploaded_clips,
    clip_index,
    start,
    end,
    duration,
):
    client, service = app_client(tmp_path)
    clip = uploaded_clips[clip_index]
    content = clip.read_bytes()
    headers = {
        "Idempotency-Key": f"upload-test-{clip_index}",
        "X-Content-SHA256": hashlib.sha256(content).hexdigest(),
    }
    form = {
        "feedback": "Apply a center punch-in to the selected section.",
        "start_seconds": start,
        "end_seconds": end,
    }
    response = client.post(
        "/api/runs/upload",
        data=form,
        files={"file": ("내 영상.mp4", content, "video/mp4")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["state"] == "EVIDENCE_ANCHORED", run
    assert run["asset"]["source_kind"] == "upload"
    assert run["asset"]["asset_id"] == run["run_id"]
    assert run["asset"]["width"] == 1280 and run["asset"]["height"] == 720
    assert run["asset"]["duration_seconds"] == pytest.approx(duration, abs=0.015)
    assert run["evidence"][0]["source"] == "user.selected_range"
    assert run["evidence"][0]["transcript"] == ""
    assert run["evidence"][0]["time_range"] == {"start_seconds": start, "end_seconds": end}
    assert run["edit_memory"] is None
    assert client.get(run["asset"]["source_url"]).status_code == 200
    replay = client.post(
        "/api/runs/upload",
        data=form,
        files={"file": ("clip.mp4", content, "video/mp4")},
        headers=headers,
    )
    assert replay.json()["run_id"] == run["run_id"]
    source_id = run["run_id"]
    service.generate_previews(source_id, selected_note_id=run["notes"][0]["note_id"])
    approved = service.approve(source_id, ApprovalRequest(candidate_id="B"))
    assert approved.spec.schema_version == "2.1"
    assert (
        approved.spec.manifest_for("locked_audio").time_range.end_seconds
        == run["asset"]["duration_seconds"]
    )
    result = service.render_approved_version(source_id)
    assert result.state == "READY", result.model_dump_json()
    assert all(check.verdict == "PASS" for check in result.proof.checks)
    assert result.proof.checks[1].label == "Full video follows the approved edit"
    assert not result.delivery_approved
    assert result.change_map.status == "ready"
    assert not any(w.status == "review" for w in result.change_map.windows)
    assert client.get(result.generated_version_url).status_code == 200
    service.fixture_locator.locate.assert_not_called()
    assert not list(tmp_path.glob("source-upload-*"))
    with pytest.raises(ValueError, match="Sample revisions"):
        service.verify_demo_version(run_id=source_id, version_label="v3")
    if clip_index == 0:
        altered = tmp_path / "outside-edit.mp4"
        service.executor.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(service.repository.version_path(source_id)),
                "-vf",
                "drawbox=x=0:y=0:w=iw:h=ih:color=red:t=fill:enable='between(t,10,11)'",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-c:a",
                "copy",
                str(altered),
            ],
            expected_output=altered,
        )
        proof = service.verifier.verify(
            source=service.repository.source_path(source_id),
            candidate=altered,
            spec=approved.spec,
            version_label="changed-outside-selection",
        )
        assert not proof.publish_allowed
        assert proof.checks[1].failure_code == "UNEXPECTED_VIDEO_CHANGE"


@pytest.mark.asyncio
async def test_live_review_retry_keeps_uploaded_source_and_selected_range(
    tmp_path, uploaded_clips, monkeypatch
):
    from revisionproof.evidence.live import VertexGeminiInterpreter

    settings = Settings(
        _env_file=None,
        mode=ExecutionMode.LIVE,
        runtime_dir=tmp_path,
        google_cloud_project="test-only",
        gcs_bucket="test-only",
        clickhouse_host="unused",
        clickhouse_writer_password="test-only",
        clickhouse_mcp_password="test-only",
    )
    service = RevisionProofService(settings, InMemoryRunRepository())
    feedback = "Apply a center punch-in to the selected section."
    selected = TimeRange(start_seconds=0, end_seconds=4)
    mock_interpret = AsyncMock(
        side_effect=[RuntimeError("simulated interruption"), interpret_selected_range(feedback)]
    )
    monkeypatch.setattr(VertexGeminiInterpreter, "interpret_many", mock_interpret)
    content = uploaded_clips[1].read_bytes()
    snapshot = await service.create_uploaded_run(
        stream=io.BytesIO(content),
        size=len(content),
        filename="retry.mp4",
        feedback=feedback,
        selected_range=selected,
        content_sha256=hashlib.sha256(content).hexdigest(),
        idempotency_key="upload-retry-test",
    )
    assert snapshot.state == "FAILED"
    source_path = service.repository.source_path(snapshot.run_id)
    original_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    retried = await service.retry_live_interpretation(snapshot.run_id, "retry-upload-review")
    assert retried.state == "EVIDENCE_ANCHORED"
    assert retried.evidence[0].source == "user.selected_range"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == original_hash
    mock_interpret.assert_awaited_with(feedback, selected_range=selected)


def test_oversize_content_length_rejected_before_multipart(tmp_path):
    client, service = app_client(tmp_path)
    response = client.post(
        "/api/runs/upload", content=b"x", headers={"Content-Length": str(25 * 1048576)}
    )
    assert response.status_code == 413
    assert "24 MiB" in response.json()["detail"]
    assert not service._create_timestamps


def test_actual_stream_size_and_checksum_enforced(tmp_path):
    with pytest.raises(SourceUploadError, match="too large"):
        copy_source(io.BytesIO(b"123456"), tmp_path / "large", 5, "a" * 64)
    assert (tmp_path / "large").stat().st_size <= 5
    with pytest.raises(SourceUploadError, match="incomplete"):
        copy_source(io.BytesIO(b"123"), tmp_path / "hash", 5, "a" * 64)


@pytest.mark.parametrize(
    "duration,start,end", [(61, 0, 6), (3, 0, 3), (12, 10, 16), (12, 0, 9), (float("nan"), 0, 6)]
)
def test_source_and_range_limits(duration, start, end):
    info = MediaInfo(
        duration_seconds=duration,
        width=1920,
        height=1080,
        video_codec="h264",
        audio_codec="aac",
        format_name="mov,mp4",
    )
    with pytest.raises(SourceUploadError):
        validate_source(
            info, TimeRange(start_seconds=start, end_seconds=end), Settings(_env_file=None)
        )


def test_corrupt_upload_does_not_create_run_or_leave_files(tmp_path):
    client, service = app_client(tmp_path)
    data = b"this is not a video"
    response = client.post(
        "/api/runs/upload",
        data={"feedback": "Apply a center punch-in.", "start_seconds": 0, "end_seconds": 6},
        files={"file": ("broken.mp4", data, "video/mp4")},
        headers={
            "Idempotency-Key": "bad-source-test",
            "X-Content-SHA256": hashlib.sha256(data).hexdigest(),
        },
    )
    assert response.status_code == 422
    assert "could not be read" in response.json()["detail"]
    assert not list(tmp_path.iterdir())
