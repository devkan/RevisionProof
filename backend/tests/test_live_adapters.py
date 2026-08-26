from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from revisionproof.evidence.live import GcsObjectStore, VertexGeminiInterpreter
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
