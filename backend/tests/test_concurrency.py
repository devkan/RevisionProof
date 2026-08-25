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


@pytest.mark.asyncio
async def test_second_media_pipeline_request_fails_fast(
    service: RevisionProofService,
) -> None:
    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    assert service._media_slot.acquire(blocking=False)  # noqa: SLF001
    try:
        with pytest.raises(ValueError, match="media pipeline is busy"):
            service.generate_previews(snapshot.run_id)
    finally:
        service._media_slot.release()  # noqa: SLF001


@pytest.mark.asyncio
async def test_idempotency_replays_same_mutation_and_rejects_key_reuse(
    service: RevisionProofService,
) -> None:
    request = CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    first = await service.create_run(request, "create:stable-demo-key")
    replay = await service.create_run(request, "create:stable-demo-key")
    assert replay.run_id == first.run_id

    with pytest.raises(ValueError, match="different request"):
        await service.create_run(
            CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Bring the product reveal closer"),
            "create:stable-demo-key",
        )

    rendered = service.generate_previews(first.run_id, f"{first.run_id}:previews")
    event_count = len(rendered.events)
    replayed_render = service.generate_previews(first.run_id, f"{first.run_id}:previews")
    assert replayed_render.run_id == first.run_id
    assert len(replayed_render.events) == event_count
