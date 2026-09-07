from __future__ import annotations

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import ApprovalRequest, CreateRunRequest
from revisionproof.service import RevisionProofService

THREE_NOTES = (
    '1. When the presenter says "RevisionProof," push in slightly.\n'
    "2. Make the middle feel more dynamic.\n"
    "3. Add B-roll that feels more premium and on-brand."
)


@pytest.mark.asyncio
async def test_baseline_proof_is_computed_once_per_approved_run(
    service: RevisionProofService, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    original_verify = service.verifier.verify
    calls = 0

    def counted_verify(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original_verify(*args, **kwargs)

    monkeypatch.setattr(service.verifier, "verify", counted_verify)

    first = service._baseline_proof_for(snapshot)  # noqa: SLF001
    second = service._baseline_proof_for(snapshot)  # noqa: SLF001

    assert calls == 1
    assert second is first


@pytest.mark.asyncio
async def test_cached_baseline_must_match_the_frozen_spec(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback=THREE_NOTES)
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="A"))
    baseline = service._baseline_proof_for(snapshot)  # noqa: SLF001
    service._baseline_proofs[snapshot.run_id] = baseline.model_copy(  # noqa: SLF001
        update={"spec_hash": "wrong-spec-hash"}
    )

    with pytest.raises(RuntimeError, match="does not match the approved spec"):
        service._baseline_proof_for(snapshot)  # noqa: SLF001
