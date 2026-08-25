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
            version_label="v2",
            stream=stream,
            size=v2.stat().st_size,
        )

    with pytest.raises(MediaCommandError):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="broken",
            stream=io.BytesIO(b"not an mp4"),
            size=10,
        )
    broken = runtime_dir / "runs" / snapshot.run_id / "versions" / "broken.mp4"
    assert not broken.exists()


def test_public_media_allowlist_never_exposes_uploaded_versions() -> None:
    with pytest.raises(Exception, match="404"):
        resolve_public_media("runs/01J00000000000000000000000/versions/client-export.mp4")
    with pytest.raises(Exception, match="404"):
        resolve_public_media("../.env")
