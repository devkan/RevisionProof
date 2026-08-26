import asyncio
from pathlib import Path

import pytest
from starlette.requests import ClientDisconnect, Request

from revisionproof.api import as_http_error, get_run_events
from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    RunSnapshot,
    RunState,
)
from revisionproof.repository import (
    InMemoryRunRepository,
    RunCapacityBusyError,
    RunNotFoundError,
)
from revisionproof.service import RateLimitError, RevisionProofService
from revisionproof.settings import Settings


def test_repository_evicts_the_oldest_inactive_run(runtime_dir: Path) -> None:
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
    repository.remember_idempotent("create", "first-key", "first-hash", first.run_id)
    second = first.model_copy(update={"run_id": "01J00000000000000000000001"})
    repository.create(second, runtime_dir / "demo" / "revisionproof_v1.mp4")

    with pytest.raises(RunNotFoundError):
        repository.get(first.run_id)
    assert repository.get(second.run_id).run_id == second.run_id
    assert repository.recall_idempotent("create", "first-key", "first-hash") is None


def test_repository_never_evicts_an_active_run(runtime_dir: Path) -> None:
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

    with repository.locked(first.run_id), pytest.raises(RunCapacityBusyError) as caught:
        repository.create(
            first.model_copy(update={"run_id": "01J00000000000000000000001"}),
            runtime_dir / "demo" / "revisionproof_v1.mp4",
        )
    http_error = as_http_error(caught.value)
    assert http_error.status_code == 429
    assert http_error.headers == {"Retry-After": "5"}


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

    with pytest.raises(RateLimitError, match="rate limit") as caught:
        await service.create_run(request)
    http_error = as_http_error(caught.value)
    assert http_error.status_code == 429
    assert http_error.headers == {"Retry-After": "60"}


@pytest.mark.asyncio
async def test_rejected_asset_does_not_consume_new_run_quota(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(
            mode=ExecutionMode.FIXTURE,
            runtime_dir=runtime_dir,
            max_new_runs_per_minute=1,
        ),
        InMemoryRunRepository(max_runs=4),
    )
    with pytest.raises(ValueError, match="allowlist"):
        await service.create_run(
            CreateRunRequest(
                asset_id="01J00000000000000000000999",
                feedback="Make the reveal more intentional",
            )
        )

    accepted = await service.create_run(
        CreateRunRequest(
            asset_id=DEMO_ASSET_ID,
            feedback="Make the reveal more intentional",
        )
    )

    assert accepted.run_id


@pytest.mark.asyncio
async def test_sse_iterator_stops_after_terminal_event(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime_dir),
        InMemoryRunRepository(max_runs=2),
    )
    snapshot = await service.create_run(
        CreateRunRequest(
            asset_id=DEMO_ASSET_ID,
            feedback="Make the reveal more intentional",
        )
    )
    snapshot.state = RunState.FAILED
    service.repository.append_event(snapshot.run_id, RunState.FAILED, "terminal")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": f"/api/runs/{snapshot.run_id}/events",
        "raw_path": b"",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
    }
    response = get_run_events(snapshot.run_id, Request(scope), service)
    try:
        chunks = [chunk async for chunk in response.body_iterator]
    finally:
        service.repository.release_active(snapshot.run_id)

    assert any('"state":"FAILED"' in chunk for chunk in chunks)
    assert chunks[-1].startswith("id:")


@pytest.mark.asyncio
async def test_sse_start_failure_releases_the_active_run_lease(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime_dir),
        InMemoryRunRepository(max_runs=1),
    )
    request_payload = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    first = await service.create_run(request_payload)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": f"/api/runs/{first.run_id}/events",
        "raw_path": b"",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
    }
    response = get_run_events(first.run_id, Request(scope), service)

    async def receive():
        return {"type": "http.disconnect"}

    async def fail_send(message):
        raise ConnectionError("simulated response-start failure")

    with pytest.raises(ClientDisconnect):
        await response(scope, receive, fail_send)

    second = await service.create_run(request_payload)
    assert service.repository.get(second.run_id).run_id == second.run_id


@pytest.mark.asyncio
async def test_concurrent_create_never_evicts_an_initializing_run(
    runtime_dir: Path, monkeypatch
) -> None:
    settings = Settings(
        mode=ExecutionMode.LIVE,
        runtime_dir=runtime_dir,
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
        clickhouse_host="clickhouse.example",
        clickhouse_writer_password="writer",
        clickhouse_mcp_password="reader",
    )
    service = RevisionProofService(settings, InMemoryRunRepository(max_runs=1))
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    entered = asyncio.Event()
    release = asyncio.Event()

    async def slow_live_interpretation(snapshot, raw_feedback):
        assert raw_feedback == request.feedback
        entered.set()
        await release.wait()

    monkeypatch.setattr(service, "_run_live_interpretation", slow_live_interpretation)
    first_task = asyncio.create_task(service.create_run(request, "first-create"))
    await entered.wait()
    try:
        with pytest.raises(ValueError, match="temporarily busy"):
            await service.create_run(request, "second-create")
    finally:
        release.set()
    first = await first_task

    assert service.repository.get(first.run_id).run_id == first.run_id
    replay = await service.create_run(request, "first-create")
    assert replay.run_id == first.run_id


@pytest.mark.asyncio
async def test_eviction_removes_the_exact_run_workspace(runtime_dir: Path) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime_dir),
        InMemoryRunRepository(max_runs=1),
    )
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    first = await service.create_run(request)
    service.generate_previews(first.run_id)
    first_run_root = runtime_dir / "runs" / first.run_id
    assert first_run_root.exists()

    await service.create_run(request)

    assert not first_run_root.exists()


@pytest.mark.asyncio
async def test_transient_eviction_cleanup_failure_does_not_fail_create(
    runtime_dir: Path, monkeypatch
) -> None:
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime_dir),
        InMemoryRunRepository(max_runs=1),
    )
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    await service.create_run(request, "first-create")
    original_cleanup = service._cleanup_evicted_run  # noqa: SLF001
    attempts = 0

    def fail_once(run_id: str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("transient filesystem error")
        original_cleanup(run_id)

    monkeypatch.setattr(service, "_cleanup_evicted_run", fail_once)
    second = await service.create_run(request, "second-create")

    assert service.repository.get(second.run_id).run_id == second.run_id
    replay = await service.create_run(request, "second-create")
    assert replay.run_id == second.run_id
    assert attempts == 1
    third = await service.create_run(request, "third-create")
    assert service.repository.get(third.run_id).run_id == third.run_id
    assert attempts == 3


@pytest.mark.asyncio
async def test_run_retains_only_the_latest_verification_artifacts(
    runtime_dir: Path,
) -> None:
    service = RevisionProofService(
        Settings(
            mode=ExecutionMode.FIXTURE,
            runtime_dir=runtime_dir,
            max_verification_attempts_per_run=2,
        ),
        InMemoryRunRepository(max_runs=2),
    )
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )
    snapshot = await service.create_run(request)
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    fixture = runtime_dir / "demo" / "revisionproof_v2_blocked.mp4"

    for label in ("blocked_1", "blocked_2"):
        with fixture.open("rb") as stream:
            snapshot = service.upload_and_verify(
                run_id=snapshot.run_id,
                version_label=label,
                stream=stream,
                size=fixture.stat().st_size,
            )
        assert snapshot.state is RunState.BLOCKED

    run_root = runtime_dir / "runs" / snapshot.run_id
    assert [path.name for path in (run_root / "versions").iterdir()] == ["blocked_2.mp4"]
    assert {path.name for path in (run_root / "evidence").iterdir()} == {
        "baseline-cta.png",
        "blocked_2-cta.png",
    }
    with (
        fixture.open("rb") as stream,
        pytest.raises(ValueError, match="verification attempt limit"),
    ):
        service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="blocked_3",
            stream=stream,
            size=fixture.stat().st_size,
        )


@pytest.mark.asyncio
async def test_concurrent_create_never_evicts_a_retrying_run(
    runtime_dir: Path, monkeypatch
) -> None:
    settings = Settings(
        mode=ExecutionMode.LIVE,
        runtime_dir=runtime_dir,
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
        clickhouse_host="clickhouse.example",
        clickhouse_writer_password="writer",
        clickhouse_mcp_password="reader",
    )
    service = RevisionProofService(settings, InMemoryRunRepository(max_runs=1))
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback="Make the reveal more intentional",
    )

    async def fail_interpretation(snapshot, raw_feedback):
        raise TimeoutError

    monkeypatch.setattr(service, "_run_live_interpretation", fail_interpretation)
    failed = await service.create_run(request, "failed-create")
    entered = asyncio.Event()
    release = asyncio.Event()

    async def slow_retry(snapshot, raw_feedback):
        entered.set()
        await release.wait()

    monkeypatch.setattr(service, "_run_live_interpretation", slow_retry)
    retry_task = asyncio.create_task(
        service.retry_live_interpretation(failed.run_id, "retry-stable")
    )
    await entered.wait()
    try:
        with pytest.raises(RunCapacityBusyError):
            await service.create_run(request, "second-create")
    finally:
        release.set()
    retried = await retry_task

    assert service.repository.get(retried.run_id).run_id == failed.run_id


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
