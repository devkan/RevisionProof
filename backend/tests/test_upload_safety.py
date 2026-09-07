import io
from pathlib import Path

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import ApprovalRequest, CreateRunRequest
from revisionproof.main import resolve_public_media
from revisionproof.media.executor import MediaCommandError
from revisionproof.service import RevisionProofService


@pytest.mark.asyncio
async def test_version_label_cannot_escape_run_directory(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="A"))

    with pytest.raises(ValueError, match="version_label"):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="../../escaped",
            stream=io.BytesIO(b"not video"),
            size=9,
        )


@pytest.mark.asyncio
async def test_invalid_media_is_removed_after_blocked_retry(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    v2 = runtime_dir / "demo" / "revisionproof_v2_blocked.mp4"
    with v2.open("rb") as stream:
        snapshot = service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="same",
            stream=stream,
            size=v2.stat().st_size,
        )
    saved = runtime_dir / "runs" / snapshot.run_id / "versions" / "same.mp4"
    saved_bytes = saved.read_bytes()

    with pytest.raises(MediaCommandError):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="same",
            stream=io.BytesIO(b"not an mp4"),
            size=10,
        )
    assert saved.read_bytes() == saved_bytes
    assert service.repository.version_path(snapshot.run_id) == saved
    assert not list(saved.parent.glob(".upload-*.mp4"))


@pytest.mark.asyncio
async def test_partial_stream_failure_never_leaves_a_version_file(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="A"))

    class BrokenStream(io.BytesIO):
        def __init__(self) -> None:
            super().__init__(b"partial bytes")
            self._failed = False

        def read(self, size: int = -1) -> bytes:
            if self._failed:
                raise OSError("simulated stream failure")
            self._failed = True
            return super().read(size)

    with pytest.raises(OSError, match="simulated stream failure"):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="partial",
            stream=BrokenStream(),
            size=13,
        )

    versions = runtime_dir / "runs" / snapshot.run_id / "versions"
    assert not list(versions.iterdir())


@pytest.mark.asyncio
async def test_upload_idempotency_requires_content_hash(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    v2 = runtime_dir / "demo" / "revisionproof_v2_blocked.mp4"
    with v2.open("rb") as stream, pytest.raises(ValueError, match="X-Content-SHA256"):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v2",
            stream=stream,
            size=v2.stat().st_size,
            idempotency_key=f"{snapshot.run_id}:version:v2",
        )
    with v2.open("rb") as stream, pytest.raises(ValueError, match="does not match"):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v2",
            stream=stream,
            size=v2.stat().st_size,
            idempotency_key=f"{snapshot.run_id}:version:v2",
            content_sha256="0" * 64,
        )


def test_public_media_allowlist_never_exposes_uploaded_versions() -> None:
    with pytest.raises(Exception, match="404"):
        resolve_public_media("runs/01J00000000000000000000000/versions/client-export.mp4")
    with pytest.raises(Exception, match="404"):
        resolve_public_media("../.env")
