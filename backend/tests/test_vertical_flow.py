from pathlib import Path

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    RunState,
    SafetyClassification,
    Verdict,
)
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings
from revisionproof.verification.service import apply_mcp_feature_diff

THREE_NOTES = (
    '1. When the presenter says "RevisionProof," push in slightly.\n'
    "2. Make the middle feel more dynamic.\n"
    "3. Add B-roll that feels more premium and on-brand."
)


@pytest.mark.asyncio
async def test_real_media_v2_blocks_then_v3_passes(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    assert snapshot.state is RunState.EVIDENCE_ANCHORED
    assert snapshot.feedback is not None
    assert snapshot.feedback.interpreter_source == "fixture.interpreter"
    assert [note.classification for note in snapshot.notes] == [
        SafetyClassification.AUTO_PREVIEWABLE,
        SafetyClassification.NEEDS_CLARIFICATION,
        SafetyClassification.MANUAL_CREATIVE,
    ]
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
    assert len(verdicts["locked_cta"].evidence_urls) == 2
    assert all(
        (runtime_dir / url.removeprefix("/media/")).exists()
        for url in verdicts["locked_cta"].evidence_urls
    )
    assert verdicts["locked_audio"].verdict is Verdict.PASS
    with pytest.raises(ValueError, match="requires a READY proof"):
        service.approve_for_delivery(snapshot.run_id)

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
    mcp_reconciled = snapshot.proof.model_copy(deep=True)
    apply_mcp_feature_diff(
        mcp_reconciled,
        snapshot.spec,
        [
            {"feature_name": "patch_similarity", "baseline_value": 0, "current_value": 1},
            {"feature_name": "patch_passing_ratio", "baseline_value": 0, "current_value": 1},
            {"feature_name": "patch_winner_margin", "baseline_value": 0, "current_value": 0.1},
            {"feature_name": "cta_passing_ratio", "baseline_value": 1, "current_value": 0},
            {"feature_name": "audio_rms_dbfs", "baseline_value": -18, "current_value": -18},
            {"feature_name": "audio_peak_dbfs", "baseline_value": -3, "current_value": -3},
        ],
    )
    assert mcp_reconciled.publish_allowed is False
    assert (
        next(
            check for check in mcp_reconciled.checks if check.check_id == "locked_cta"
        ).failure_code
        == "LOCKED_OVERLAY_MISSING"
    )
    snapshot = service.approve_for_delivery(snapshot.run_id)
    assert snapshot.delivery_approved is True


@pytest.mark.asyncio
async def test_offline_rehearsal_is_read_only(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.OFFLINE_REHEARSAL, runtime_dir=runtime_dir),
        InMemoryRunRepository(),
    )
    with pytest.raises(ValueError, match="read-only"):
        await service.create_run(CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES))
