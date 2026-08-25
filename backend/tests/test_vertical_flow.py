from pathlib import Path

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import ApprovalRequest, CreateRunRequest, RunState, Verdict
from revisionproof.service import RevisionProofService


@pytest.mark.asyncio
async def test_real_media_v2_blocks_then_v3_passes(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(
            asset_id=DEMO_ASSET_ID, feedback="Make the product reveal feel intentional"
        )
    )
    assert snapshot.state is RunState.EVIDENCE_ANCHORED
    assert snapshot.feedback is not None
    assert snapshot.feedback.interpreter_source == "fixture.interpreter"
    assert snapshot.evidence[0].source == "fixture.segment_index"

    snapshot = service.generate_previews(snapshot.run_id)
    assert snapshot.state is RunState.PREVIEWS_READY
    assert all(
        (runtime_dir / item.preview_url.removeprefix("/media/")).exists()
        for item in snapshot.candidates
    )

    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    assert snapshot.state is RunState.HUMAN_APPROVED
    assert snapshot.spec is not None
    frozen_hash = snapshot.spec.spec_hash

    v2 = runtime_dir / "demo" / "revisionproof_v2_blocked.mp4"
    with v2.open("rb") as stream:
        snapshot = service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v2",
            stream=stream,
            size=v2.stat().st_size,
        )
    assert snapshot.state is RunState.BLOCKED
    assert snapshot.proof is not None
    assert snapshot.proof.publish_allowed is False
    assert snapshot.proof.spec_hash == frozen_hash
    verdicts = {check.check_id: check for check in snapshot.proof.checks}
    assert verdicts["approved_patch"].verdict is Verdict.PASS
    assert verdicts["locked_cta"].verdict is Verdict.FAIL
    assert verdicts["locked_cta"].failure_code == "LOCKED_OVERLAY_MISSING"
    assert verdicts["locked_audio"].verdict is Verdict.PASS

    v3 = runtime_dir / "demo" / "revisionproof_v3_ready.mp4"
    with v3.open("rb") as stream:
        snapshot = service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v3",
            stream=stream,
            size=v3.stat().st_size,
        )
    assert snapshot.state is RunState.READY
    assert snapshot.proof is not None
    assert snapshot.proof.publish_allowed is True
    assert all(check.verdict is Verdict.PASS for check in snapshot.proof.checks)
    assert snapshot.spec is not None and snapshot.spec.spec_hash == frozen_hash
