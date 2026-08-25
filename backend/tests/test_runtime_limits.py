from pathlib import Path

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import CreateRunRequest, ExecutionMode, RunSnapshot, RunState
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings


def test_repository_rejects_runs_beyond_capacity(runtime_dir: Path) -> None:
    repository = InMemoryRunRepository(max_runs=1)
    first = RunSnapshot(
        run_id="01J00000000000000000000000",
        asset={
            "asset_id": DEMO_ASSET_ID,
            "title": "demo",
            "source_url": "/media/demo/revisionproof_v1.mp4",
            "duration_seconds": 30,
            "width": 1280,
            "height": 720,
            "codec": "h264",
        },
        mode=ExecutionMode.FIXTURE,
        state=RunState.INDEXED,
    )
    repository.create(first, runtime_dir / "demo" / "revisionproof_v1.mp4")

    with pytest.raises(ValueError, match="run capacity reached"):
        repository.create(
            first.model_copy(update={"run_id": "01J00000000000000000000001"}),
            runtime_dir / "demo" / "revisionproof_v1.mp4",
        )


@pytest.mark.asyncio
async def test_new_run_rate_limit_bounds_public_demo_work(runtime_dir: Path) -> None:
    settings = Settings(
        mode=ExecutionMode.FIXTURE,
        runtime_dir=runtime_dir,
        max_new_runs_per_minute=1,
    )
    service = RevisionProofService(settings, InMemoryRunRepository(max_runs=4))
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    await service.create_run(request)

    with pytest.raises(ValueError, match="rate limit"):
        await service.create_run(request)


@pytest.mark.asyncio
async def test_live_retry_reuses_preserved_feedback(runtime_dir: Path, monkeypatch) -> None:
    settings = Settings(
        mode=ExecutionMode.LIVE,
        runtime_dir=runtime_dir,
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
        clickhouse_host="clickhouse.example",
        clickhouse_writer_password="writer",
        clickhouse_mcp_password="reader",
    )
    service = RevisionProofService(settings, InMemoryRunRepository())
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )

    async def fail_once(snapshot, raw_feedback):
        assert raw_feedback == request.feedback
        raise TimeoutError

    monkeypatch.setattr(service, "_run_live_interpretation", fail_once)
    failed = await service.create_run(request)
    assert failed.state is RunState.FAILED
    assert failed.retryable is True

    async def succeed(snapshot, raw_feedback):
        assert raw_feedback == request.feedback
        service._transition(snapshot, RunState.NOTES_PARSED, "retry succeeded")  # noqa: SLF001

    monkeypatch.setattr(service, "_run_live_interpretation", succeed)
    retried = await service.retry_live_interpretation(failed.run_id, "retry:stable-key")

    assert retried.state is RunState.NOTES_PARSED
    assert retried.retryable is False
    assert retried.error is None
    assert [event.state for event in retried.events[-2:]] == [
        RunState.INDEXED,
        RunState.NOTES_PARSED,
    ]
