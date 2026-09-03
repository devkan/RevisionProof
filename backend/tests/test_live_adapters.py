from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from revisionproof.contracts import ParsedFeedback, SafetyClassification, TimeRange
from revisionproof.evidence.live import (
    GcsObjectStore,
    LiveEvidenceLocator,
    VertexGeminiInterpreter,
)
from revisionproof.settings import Settings


class FakeBlob:
    def __init__(self, *, exists: bool, size: int = 0, metadata=None) -> None:
        self._exists = exists
        self.size = size
        self.metadata = metadata
        self.uploads: list[tuple] = []

    def exists(self, *, client) -> bool:
        assert client is not None
        return self._exists

    def reload(self, *, client) -> None:
        assert client is not None

    def upload_from_filename(self, path, *, content_type, if_generation_match) -> None:
        self.uploads.append((path, content_type, if_generation_match))


class FakeStorageClient:
    def __init__(self, blob: FakeBlob) -> None:
        self.blob = blob
        self.closed = False

    def bucket(self, name):
        assert name == "revisionproof-test-media"
        return SimpleNamespace(blob=lambda _object_name: self.blob)

    def close(self) -> None:
        self.closed = True


def test_gcs_upload_is_create_only_and_hash_idempotent(runtime_dir: Path, monkeypatch) -> None:
    source = runtime_dir / "test-gcs-create-only.mp4"
    source.write_bytes(b"revisionproof-candidate")
    blob = FakeBlob(exists=False)
    client = FakeStorageClient(blob)
    monkeypatch.setattr("google.cloud.storage.Client", lambda **_kwargs: client)
    settings = Settings(
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
    )

    uri = GcsObjectStore(settings).upload(source, "runs/run-1/candidate.mp4")

    assert uri == "gs://revisionproof-test-media/runs/run-1/candidate.mp4"
    assert blob.metadata == {
        "app": "revisionproof",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    assert blob.uploads == [(str(source), "video/mp4", 0)]
    assert client.closed is True
    source.unlink()


def test_gcs_upload_reuses_only_an_exact_existing_object(runtime_dir: Path, monkeypatch) -> None:
    source = runtime_dir / "test-gcs-idempotent.mp4"
    source.write_bytes(b"stable")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    blob = FakeBlob(exists=True, size=source.stat().st_size, metadata={"sha256": digest})
    client = FakeStorageClient(blob)
    monkeypatch.setattr("google.cloud.storage.Client", lambda **_kwargs: client)
    settings = Settings(
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
    )

    GcsObjectStore(settings).upload(source, "runs/run-1/candidate.mp4")

    assert blob.uploads == []
    assert client.closed is True

    drifted_blob = FakeBlob(exists=True, size=source.stat().st_size, metadata={"sha256": "wrong"})
    drifted_client = FakeStorageClient(drifted_blob)
    monkeypatch.setattr("google.cloud.storage.Client", lambda **_kwargs: drifted_client)
    with pytest.raises(RuntimeError, match="refusing to overwrite drifted object"):
        GcsObjectStore(settings).upload(source, "runs/run-1/candidate.mp4")
    assert drifted_client.closed is True
    source.unlink()


def test_vertex_embedding_client_is_closed(monkeypatch) -> None:
    class FakeGenaiClient:
        def __init__(self, **_kwargs) -> None:
            self.models = SimpleNamespace(
                embed_content=lambda **_arguments: SimpleNamespace(
                    embeddings=[SimpleNamespace(values=[0.0] * 768)]
                )
            )
            self.closed = False

        def close(self) -> None:
            self.closed = True

    client = FakeGenaiClient()
    monkeypatch.setattr("google.genai.Client", lambda **_kwargs: client)

    values = VertexGeminiInterpreter(Settings(google_cloud_project="revisionproof-test")).embed(
        "RevisionProof"
    )

    assert len(values) == 768
    assert client.closed is True


def test_vertex_adk_model_pins_vertex_project_without_global_env(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeGenaiClient:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    for name in (
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_GENAI_USE_ENTERPRISE",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("google.genai.Client", FakeGenaiClient)

    model = VertexGeminiInterpreter(
        Settings(
            google_cloud_project="revisionproof-test",
            google_cloud_location="global",
        )
    )._adk_model()

    assert model.model == "gemini-3.5-flash-lite"
    assert model.api_client is model.api_client
    assert captured == {
        "vertexai": True,
        "project": "revisionproof-test",
        "location": "global",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("uploaded,compound", [(False, False), (True, False), (True, True)])
async def test_vertex_interpretation_closes_runner_and_both_clients(
    monkeypatch, uploaded, compound
) -> None:
    closed = {"runner": False, "async_client": False, "sync_client": False}
    raw_text = (
        "4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시"
        if compound
        else "선택한 구간을 중앙 기준으로 확대해 주세요."
        if uploaded
        else 'When the presenter says "RevisionProof," push in slightly.'
    )

    class FakeAsyncClient:
        async def aclose(self) -> None:
            closed["async_client"] = True

    class FakeGenaiClient:
        def __init__(self, **_kwargs) -> None:
            self.aio = FakeAsyncClient()

        def close(self) -> None:
            closed["sync_client"] = True

    class FakeAgent:
        def __init__(self, **kwargs) -> None:
            self.model = kwargs["model"]

    class FakeSessionService:
        async def create_session(self, **_kwargs):
            return SimpleNamespace(id="01J00000000000000000000099")

    class FakeRunner:
        def __init__(self, **_kwargs) -> None:
            self.session_service = FakeSessionService()

        async def run_async(self, **_kwargs):
            payload = {
                "notes": [
                    {
                        "raw_text": raw_text,
                        "intent": "Apply a short center punch-in",
                        "classification": "AUTO_PREVIEWABLE",
                        "confidence": 0.94,
                        "target_phrase": "selected section" if uploaded else "RevisionProof",
                        "rationale": "The phrase and supported edit are precise.",
                    }
                ]
            }
            yield SimpleNamespace(
                content=SimpleNamespace(parts=[SimpleNamespace(text=json.dumps(payload))])
            )

        async def close(self) -> None:
            closed["runner"] = True

    monkeypatch.setattr("google.genai.Client", FakeGenaiClient)
    monkeypatch.setattr("google.adk.agents.LlmAgent", FakeAgent)
    monkeypatch.setattr("google.adk.runners.InMemoryRunner", FakeRunner)

    notes = await VertexGeminiInterpreter(
        Settings(google_cloud_project="revisionproof-test")
    ).interpret_many(
        raw_text, selected_range=TimeRange(start_seconds=4, end_seconds=10) if uploaded else None
    )

    assert notes[0].raw_text == raw_text
    if compound:
        assert notes[0].classification == SafetyClassification.MANUAL_CREATIVE
        assert notes[0].target_phrase is None
    elif uploaded:
        assert notes[0].target_phrase in raw_text
        assert notes[0].classification == SafetyClassification.AUTO_PREVIEWABLE
    else:
        assert notes[0].target_phrase == "RevisionProof"
    assert closed == {"runner": True, "async_client": True, "sync_client": True}


@pytest.mark.asyncio
async def test_live_locator_normalizes_clickhouse_fixed_string_segment_ids() -> None:
    segment_id = "01J00000000000000000000002"

    class FakeInterpreter:
        def embed(self, _text: str) -> list[float]:
            return [0.0] * 768

    class FakeReader:
        async def run_query(self, _query: str):
            return [
                {
                    "segment_id": f"b'{segment_id}\\x00'",
                    "start_seconds": 8,
                    "end_seconds": 14,
                    "score": 0.93,
                    "transcript": "RevisionProof",
                    "visual_summary": "Product reveal",
                }
            ]

    feedback = ParsedFeedback(
        raw_text='When the presenter says "RevisionProof," push in slightly.',
        intent="Apply a short center punch-in",
        target_phrase="RevisionProof",
        classification=SafetyClassification.AUTO_PREVIEWABLE,
        confidence=0.94,
        rationale="The phrase and supported edit are precise.",
        interpreter_source="google.vertex.gemini",
    )

    anchors = await LiveEvidenceLocator(
        Settings(google_cloud_project="revisionproof-test"),
        FakeReader(),  # type: ignore[arg-type]
        FakeInterpreter(),  # type: ignore[arg-type]
    ).locate("01J00000000000000000000000", feedback)

    assert anchors[0].segment_id == segment_id
