from __future__ import annotations

import hashlib
import io
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from revisionproof.contracts import ExecutionMode
from revisionproof.editing.logo import save_logo
from revisionproof.editing.models import EditOperation, EditPlan, TranscriptionCue
from revisionproof.editing.render import render_plan
from revisionproof.editing.sampling import sample_plan_frame
from revisionproof.editing.transcription import GeminiTranscript, transcribe_with_gemini
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import probe_media
from revisionproof.settings import Settings
from revisionproof.verification.metrics import audio_levels_db, normalized_similarity, read_frame


@pytest.fixture(scope="module")
def advanced_media(tmp_path_factory):
    folder = tmp_path_factory.mktemp("advanced-edits")
    source = folder / "source.mp4"
    executor = MediaExecutor(90)
    executor.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x720:rate=30:duration=6",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=6",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-shortest",
            str(source),
        ],
        expected_output=source,
    )
    return folder, source, executor


def make_logo() -> bytes:
    image = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((20, 20, 580, 280), fill=(0, 240, 255, 255))
    content = io.BytesIO()
    image.save(content, "PNG")
    return content.getvalue()


def test_speed_timeline_mapping_and_conflicts():
    plan = EditPlan(
        source_duration=10,
        operations=(
            EditOperation(kind="cut", start=1, end=2),
            EditOperation(kind="speed", start=4, end=8, rate=2),
        ),
    )
    assert plan.output_duration == 7
    assert plan.source_time(1) == 2
    assert plan.source_time(3) == 4
    assert plan.source_time(4) == 6
    assert sample_plan_frame(plan, 4).requested_edit is True
    with pytest.raises(ValidationError, match="Overlapping speed"):
        EditPlan(
            source_duration=10,
            operations=(
                EditOperation(kind="speed", start=2, end=5, rate=1.5),
                EditOperation(kind="speed", start=4, end=6, rate=2),
            ),
        )
    with pytest.raises(ValidationError, match="within 60 seconds"):
        EditPlan(
            source_duration=60,
            operations=(EditOperation(kind="speed", start=0, end=60, rate=0.5),),
        )


def test_logo_is_normalized_frozen_and_rendered_with_speed_and_volume(advanced_media, tmp_path):
    _, source, executor = advanced_media
    content = make_logo()
    logo = save_logo(
        io.BytesIO(content),
        tmp_path / "logos",
        size=len(content),
        limit=2 * 1048576,
        expected_hash=hashlib.sha256(content).hexdigest(),
    )
    assert max(logo.width, logo.height) == 512
    plan = EditPlan(
        source_duration=6,
        operations=(
            EditOperation(kind="volume", start=0, end=2, volume_db=-6),
            EditOperation(kind="speed", start=2, end=4, rate=2),
            EditOperation(
                kind="logo",
                start=4,
                end=6,
                position="bottom_right",
                asset_id=logo.asset_id,
                asset_sha256=logo.sha256,
            ),
        ),
    )
    target = render_plan(
        source,
        tmp_path / "advanced.mp4",
        plan,
        "A",
        executor,
        logo_root=tmp_path / "logos",
    )
    assert probe_media(target, executor).duration_seconds == pytest.approx(5, abs=0.08)
    assert normalized_similarity(read_frame(source, 3), read_frame(target, 2.5)) > 0.96
    before = audio_levels_db(target, start_seconds=0.2, duration_seconds=1, executor=executor)
    after = audio_levels_db(target, start_seconds=3.2, duration_seconds=1, executor=executor)
    assert after[0] - before[0] == pytest.approx(6, abs=1)
    original_corner = read_frame(source, 4.5)[500:700, 980:1260]
    logo_corner = read_frame(target, 3.5)[500:700, 980:1260]
    assert np.mean(np.abs(original_corner.astype(float) - logo_corner.astype(float))) > 10
    (tmp_path / "logos" / f"{logo.asset_id}.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        render_plan(
            source,
            tmp_path / "changed.mp4",
            plan,
            "A",
            executor,
            logo_root=tmp_path / "logos",
        )


@pytest.mark.asyncio
async def test_mixed_language_transcription_uses_audio_and_returns_reviewable_cues(
    monkeypatch, tmp_path
):
    captured = {}

    class FakeModels:
        async def generate_content(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                parsed=GeminiTranscript(
                    detected_languages=["ko", "en"],
                    cues=[
                        TranscriptionCue(
                            start=0, end=1.2, text="안녕하세요 KANAPP", language="mixed"
                        ),
                        TranscriptionCue(
                            start=1.2, end=2.4, text="AI, made practical.", language="en"
                        ),
                    ],
                ),
                text="",
            )

    class FakeAsync:
        models = FakeModels()

        async def aclose(self):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.aio = FakeAsync()

        def close(self):
            return None

    monkeypatch.setattr("google.genai.Client", FakeClient)
    audio = tmp_path / "speech.wav"
    audio.write_bytes(b"RIFF-test-audio")
    result = await transcribe_with_gemini(
        audio,
        duration=4,
        language="mixed",
        settings=Settings(
            _env_file=None,
            mode=ExecutionMode.LIVE,
            runtime_dir=tmp_path,
            google_cloud_project="test-project",
        ),
    )
    assert result.detected_languages == ("ko", "en")
    assert [cue.text for cue in result.cues] == ["안녕하세요 KANAPP", "AI, made practical."]
    assert "Do not translate" in captured["contents"][1].text
    assert captured["client"]["vertexai"] is True
