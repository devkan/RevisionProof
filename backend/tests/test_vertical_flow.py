from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from revisionproof.api import router
from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    RunSnapshot,
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
async def test_selected_request_builds_and_verifies_full_video(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    auto_note = next(
        note
        for note in snapshot.notes
        if note.classification is SafetyClassification.AUTO_PREVIEWABLE
    )
    snapshot = service.generate_previews(
        snapshot.run_id,
        selected_note_id=auto_note.note_id,
    )
    assert snapshot.selected_note_id == auto_note.note_id
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))

    snapshot = service.render_approved_version(
        snapshot.run_id,
        idempotency_key=f"{snapshot.run_id}:automatic-version",
    )

    assert snapshot.state is RunState.READY
    assert snapshot.generated_version_url == f"/api/runs/{snapshot.run_id}/generated-video"
    assert snapshot.proof is not None and snapshot.proof.publish_allowed is True
    assert all(check.verdict is Verdict.PASS for check in snapshot.proof.checks)
    generated = service.repository.version_path(snapshot.run_id)
    assert generated.is_file()
    assert generated.stat().st_size <= service.settings.max_upload_bytes
    assert not (runtime_dir / "runs" / snapshot.run_id / "render").exists()

    replay = service.render_approved_version(
        snapshot.run_id,
        idempotency_key=f"{snapshot.run_id}:automatic-version",
    )
    assert replay.generated_version_url == snapshot.generated_version_url

    app = FastAPI()
    app.state.service = service
    app.include_router(router)
    response = TestClient(app).get(snapshot.generated_version_url)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")


@pytest.mark.asyncio
async def test_unsupported_request_cannot_enter_preview_pipeline(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    manual_note = next(
        note
        for note in snapshot.notes
        if note.classification is SafetyClassification.MANUAL_CREATIVE
    )

    with pytest.raises(ValueError, match="select one request marked ready"):
        service.generate_previews(snapshot.run_id, selected_note_id=manual_note.note_id)


@pytest.mark.parametrize("candidate_id", ["A", "B"])
def test_demo_versions_follow_the_frozen_candidate(
    service: RevisionProofService, candidate_id: str
) -> None:
    app = FastAPI()
    app.state.service = service
    app.include_router(router)
    client = TestClient(app)
    created = client.post(
        "/api/runs",
        json={"asset_id": DEMO_ASSET_ID, "feedback": THREE_NOTES},
    )
    assert created.status_code == 201
    run_id = created.json()["run_id"]
    assert client.post(f"/api/runs/{run_id}/previews").status_code == 200
    approved = client.post(
        f"/api/runs/{run_id}/approvals",
        json={"candidate_id": candidate_id},
    )
    assert approved.status_code == 200

    v2 = client.post(f"/api/runs/{run_id}/demo-versions/v2")
    assert v2.status_code == 200
    snapshot = RunSnapshot.model_validate(v2.json())
    assert snapshot.proof is not None
    checks = {check.check_id: check for check in snapshot.proof.checks}
    assert checks["approved_patch"].verdict is Verdict.PASS
    assert checks["locked_cta"].verdict is Verdict.FAIL
    assert snapshot.state is RunState.BLOCKED

    v3 = client.post(f"/api/runs/{run_id}/demo-versions/v3")
    assert v3.status_code == 200
    snapshot = RunSnapshot.model_validate(v3.json())
    assert snapshot.state is RunState.READY
    assert snapshot.proof is not None and snapshot.proof.publish_allowed is True
    assert all(check.verdict is Verdict.PASS for check in snapshot.proof.checks)


@pytest.mark.asyncio
async def test_live_mode_rejects_demo_versions(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="A"))
    service.settings.mode = ExecutionMode.LIVE

    app = FastAPI()
    app.state.service = service
    app.include_router(router)
    response = TestClient(app).post(f"/api/runs/{snapshot.run_id}/demo-versions/v3")

    assert response.status_code == 409
    assert response.json()["detail"] == "demo versions are only available in FIXTURE mode"
    unchanged = service.repository.get(snapshot.run_id)
    assert unchanged.state is RunState.HUMAN_APPROVED
    assert unchanged.proof is None


@pytest.mark.asyncio
async def test_offline_rehearsal_is_read_only(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.OFFLINE_REHEARSAL, runtime_dir=runtime_dir),
        InMemoryRunRepository(),
    )
    with pytest.raises(ValueError, match="read-only"):
        await service.create_run(CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES))
