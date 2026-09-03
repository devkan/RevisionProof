"""Regression coverage for adjacent-frame false blocks after source-time cuts."""

import json

import cv2
import numpy as np
import pytest

from revisionproof.contracts import ApprovalRequest, ExecutionMode, TimeRange
from revisionproof.editing.models import EditOperation, EditPlan
from revisionproof.editing.verify import file_hash
from revisionproof.media.executor import MediaExecutor
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings


@pytest.fixture(scope="module")
def alternating_source(tmp_path_factory):
    source = tmp_path_factory.mktemp("frame-mapping") / "alternating.mp4"
    MediaExecutor(90).run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=black:s=1280x720:r=30:d=4,geq=lum='if(mod(N,2),235,16)':cb=128:cr=128",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-t",
            "4",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            str(source),
        ],
        expected_output=source,
    )
    return source


def frame_means(path):
    capture = cv2.VideoCapture(str(path))
    values = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                return values
            values.append(float(np.mean(frame)))
    finally:
        capture.release()


@pytest.mark.asyncio
@pytest.mark.parametrize("with_cut", [True, False])
async def test_approved_frames_do_not_false_block_after_odd_frame_cut(
    alternating_source, tmp_path, with_cut
):
    service = RevisionProofService(
        Settings(
            _env_file=None,
            mode=ExecutionMode.FIXTURE,
            runtime_dir=tmp_path,
            intelligence_enabled=True,
        ),
        InMemoryRunRepository(),
    )
    operations = (
        (EditOperation(kind="cut", start=0.1, end=0.2),)
        if with_cut
        else (EditOperation(kind="text", start=8 / 30, end=20 / 30, text="Boundary cue"),)
    )
    plan = EditPlan(source_duration=4, operations=operations)
    with alternating_source.open("rb") as stream:
        run = await service.create_uploaded_run(
            stream=stream,
            size=alternating_source.stat().st_size,
            filename="alternating.mp4",
            feedback="Review the exact selected edit.",
            selected_range=TimeRange(start_seconds=0, end_seconds=4),
            content_sha256=file_hash(alternating_source),
            idempotency_key="frame-mapping-qa",
            edit_plan=plan,
        )
    service.generate_previews(run.run_id)
    service.approve(run.run_id, ApprovalRequest(candidate_id="A"))
    service.render_approved_version(run.run_id)
    original = service.repository.source_path(run.run_id)
    export = service.repository.version_path(run.run_id)
    if with_cut:
        # A correct render removes exactly source frames 3, 4 and 5. This is an
        # independent sequential decode, without the sampler under regression.
        means = frame_means(original)
        expected = means[:3] + means[6:]
        assert len(expected) == 117
        np.testing.assert_allclose(frame_means(export), expected, atol=1)
    (tmp_path / "frame-mapping-proof.json").write_text(
        json.dumps({"state": run.state, "proof": run.proof.model_dump(mode="json")}, indent=2),
        encoding="utf-8",
    )
    assert run.proof.checks[0].measured["exact_file_match"] == 1
    assert run.state == "READY", run.proof
    assert run.change_map.status == "ready"
    assert not any(window.status == "review" for window in run.change_map.windows)
