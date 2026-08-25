from concurrent.futures import ThreadPoolExecutor

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import ApprovalRequest, CreateRunRequest, RunState
from revisionproof.service import RevisionProofService


@pytest.mark.asyncio
async def test_concurrent_approval_cannot_replace_frozen_spec(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)

    def approve(candidate_id: str):
        return service.approve(
            snapshot.run_id,
            ApprovalRequest(candidate_id=candidate_id),  # type: ignore[arg-type]
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(approve, candidate_id) for candidate_id in ("A", "B")]
        results = []
        errors = []
        for future in futures:
            try:
                results.append(future.result())
            except ValueError as exc:
                errors.append(exc)

    assert len(results) == 1
    assert len(errors) == 1
    frozen = service.repository.get(snapshot.run_id)
    assert frozen.state is RunState.HUMAN_APPROVED
    assert frozen.spec is not None
    approved_id = frozen.spec.approved_candidate.candidate_id
    assert all(result.spec.approved_candidate.candidate_id == approved_id for result in results)
