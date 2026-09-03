from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_contracts import make_spec

import revisionproof.intelligence.service as intelligence_module
from revisionproof.api import router
from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    ParsedFeedback,
    RunSnapshot,
    RunState,
    Verdict,
    VerificationCheck,
    VerificationProof,
)
from revisionproof.intelligence.models import ChangeWindow, RevisionChangeMap
from revisionproof.intelligence.service import RevisionIntelligence
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings

UNIT_VECTOR = [1.0] + [0.0] * 767
PRIVATE_KEY = "test-only-workspace-key-not-a-real-secret"


def ready_snapshot() -> RunSnapshot:
    spec = make_spec()
    proof = VerificationProof(
        version_label="v3",
        spec_hash=spec.spec_hash,
        verdict=Verdict.PASS,
        publish_allowed=True,
        checks=[
            VerificationCheck(
                check_id=manifest.check_id,
                label=manifest.check_id,
                verdict=Verdict.PASS,
                measured={},
                threshold={},
                evidence_time_range=manifest.time_range,
                evidence_urls=["/media/private-evidence-must-not-enter-memory.png"],
            )
            for manifest in spec.verification_manifest
        ],
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    return RunSnapshot(
        run_id=spec.run_id,
        asset={
            "asset_id": spec.asset_id,
            "title": "RevisionProof test asset",
            "source_url": "/media/demo/revisionproof_v1.mp4",
            "duration_seconds": 30,
            "width": 1280,
            "height": 720,
            "codec": "h264",
        },
        mode=ExecutionMode.FIXTURE,
        state=RunState.READY,
        feedback=ParsedFeedback(
            raw_text='Push in when the presenter says "RevisionProof".',
            intent="Apply a six-second center punch-in",
            target_phrase="RevisionProof",
            rationale="Supported edit on a located phrase",
            interpreter_source="fixture.interpreter",
        ),
        spec=spec,
        proof=proof,
        delivery_approved=True,
        change_map=RevisionChangeMap(
            status="ready",
            version_label="v3",
            spec_hash=spec.spec_hash,
            analysis_id="01J00000000000000000000001",
            source="fixture.frame_analysis",
            duration_seconds=30,
            windows=[
                ChangeWindow(
                    second=second,
                    sample_count=2,
                    visual_delta=0.04 if 8 <= second < 14 else 0,
                    residual_delta=0.001,
                    cta_delta=0,
                    audio_delta_db=0,
                    requested=8 <= second < 14,
                    status="requested" if 8 <= second < 14 else "unchanged",
                )
                for second in range(30)
            ],
            message="Deterministic test measurements",
        ),
    )


def manager(*, live=False, **overrides) -> RevisionIntelligence:
    values = {
        "mode": ExecutionMode.LIVE if live else ExecutionMode.FIXTURE,
        "intelligence_enabled": True,
        "memory_write_token": PRIVATE_KEY if live else None,
    }
    values.update(overrides)
    return RevisionIntelligence(Settings(_env_file=None, **values))


def memory_row(*, identity="a" * 64, distance=0.1, **overrides) -> dict:
    row = {
        "memory_id": identity,
        "distance": distance,
        "intent": "Apply a six-second center punch-in",
        "target_phrase": "RevisionProof",
        "candidate_id": "B",
        "scale": 1.12,
        "duration_seconds": 6,
        "approved_at": datetime(2026, 9, 3, tzinfo=UTC),
        "spec_hash": "b" * 64,
    }
    row.update(overrides)
    return row


def install_reader(monkeypatch, responses):
    queries: list[str] = []

    class FakeReader:
        def __init__(self, _settings):
            pass

        async def run_query(self, query):
            queries.append(query)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(intelligence_module, "McpClickHouseReader", FakeReader)
    return queries


def test_disabled_search_performs_no_embedding_or_external_lookup(monkeypatch) -> None:
    intelligence = manager(intelligence_enabled=False)
    embed = Mock(side_effect=AssertionError("disabled means no embedding"))
    monkeypatch.setattr(intelligence, "_embedding", embed)
    result = intelligence.search(ready_snapshot(), "qbit")
    assert result.status == "disabled"
    assert result.actual_engine == "unavailable"
    embed.assert_not_called()


def test_fixture_memory_requires_save_and_is_explicitly_not_live() -> None:
    intelligence = manager()
    snapshot = ready_snapshot()
    assert intelligence.search(snapshot, "hnsw").status == "empty"
    saved = intelligence.save(snapshot, None)
    assert saved.source == "fixture.approved_memory"
    assert snapshot.memory_saved is True
    assert intelligence.save(snapshot, None).status == "already_saved"
    for engine in ("exact", "hnsw", "qbit"):
        result = intelligence.search(snapshot, engine)
        assert result.status == "ready"
        assert result.actual_engine == "fixture"
        assert result.collection_size == 1
        assert result.index_verified is False
        assert result.matches[0].similarity == pytest.approx(1)
        assert result.matches[0].memory_id == saved.memory_id


def test_cached_results_are_isolated_and_forget_run_removes_embedding_and_cache() -> None:
    intelligence = manager()
    snapshot = ready_snapshot()
    intelligence.save(snapshot, None)
    first = intelligence.search(snapshot, "exact")
    first.matches.clear()
    assert len(intelligence.search(snapshot, "exact").matches) == 1
    intelligence.forget_run(snapshot.run_id)
    assert snapshot.run_id not in intelligence._embeddings  # noqa: SLF001
    assert not intelligence._search_cache  # noqa: SLF001


def test_empty_live_collection_does_not_spend_an_embedding_request(monkeypatch) -> None:
    intelligence = manager(live=True)
    queries = install_reader(monkeypatch, [[{"total": 0}]])
    embed = Mock(side_effect=AssertionError("empty library must not embed"))
    monkeypatch.setattr(intelligence, "_embedding", embed)
    result = intelligence.search(ready_snapshot(), "qbit")
    assert result.status == "empty"
    assert result.actual_engine == "none"
    assert result.collection_size == 0
    assert len(queries) == 1
    embed.assert_not_called()


@pytest.mark.parametrize(
    "count",
    [[], [{"total": -1}], [{"total": "bad"}], [{"wrong": 3}], [{"total": 0.5}], [{"total": True}]],
)
def test_live_search_malformed_count_is_unavailable_not_empty(monkeypatch, count) -> None:
    intelligence = manager(live=True)
    queries = install_reader(monkeypatch, [count])
    result = intelligence.search(ready_snapshot(), "exact")
    assert result.status == "unavailable"
    assert result.actual_engine == "unavailable"
    assert result.matches == []
    assert len(queries) == 1


@pytest.mark.parametrize(
    "count,plan,actual,verified,query_count",
    [
        (4, None, "exact", False, 2),
        (2000, "Indexes: PrimaryKey", "exact", False, 3),
        (2000, "Skip approved_edit_hnsw vector_similarity GRANULARITY 100000000", "hnsw", True, 3),
        (2000, "Skip approved_edit_hnsw but no vector type", "exact", False, 3),
    ],
)
def test_hnsw_is_advertised_only_after_actual_plan_selection(
    monkeypatch, count, plan, actual, verified, query_count
) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    responses = [[{"total": count}]]
    if plan is not None:
        responses.append([{"explain": plan}])
    responses.append([memory_row()])
    queries = install_reader(monkeypatch, responses)
    result = intelligence.search(ready_snapshot(), "hnsw")
    assert result.status == "ready"
    assert result.requested_engine == "hnsw"
    assert result.actual_engine == actual
    assert result.index_verified is verified
    assert len(queries) == query_count
    assert ("use_skip_indexes = 0" in queries[-1]) is (actual == "exact")


def test_qbit_reports_precision_and_deduplicates_weak_or_duplicate_matches(monkeypatch) -> None:
    intelligence = manager(live=True, memory_qbit_precision=24)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    queries = install_reader(
        monkeypatch,
        [[{"total": 4}], [memory_row(), memory_row(), memory_row(identity="c" * 64, distance=1.7)]],
    )
    result = intelligence.search(ready_snapshot(), "qbit")
    assert result.actual_engine == "qbit"
    assert result.precision_bits == 24
    assert result.index_verified is False
    assert len(result.matches) == 1
    assert result.matches[0].similarity == pytest.approx(0.995)
    assert "reference_vector, 24)" in queries[-1]


@pytest.mark.parametrize("distance", [-0.1, float("inf"), float("nan")])
def test_live_search_rejects_invalid_distances_without_fixture_substitution(
    monkeypatch, distance
) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    install_reader(monkeypatch, [[{"total": 1}], [memory_row(distance=distance)]])
    result = intelligence.search(ready_snapshot(), "exact")
    assert result.status == "unavailable"
    assert result.source == "mcp-clickhouse.run_query"
    assert result.matches == []


def test_live_outage_has_bounded_cache_and_can_be_retried_after_expiry(monkeypatch) -> None:
    intelligence = manager(live=True)
    clock = [0.0]
    monkeypatch.setattr(intelligence_module, "monotonic", lambda: clock[0])
    queries = install_reader(monkeypatch, [TimeoutError("sleeping service"), [{"total": 0}]])
    snapshot = ready_snapshot()
    assert intelligence.search(snapshot, "hnsw").status == "unavailable"
    assert intelligence.search(snapshot, "hnsw").status == "unavailable"
    assert len(queries) == 1
    clock[0] = 31.0
    assert intelligence.search(snapshot, "hnsw").status == "empty"
    assert len(queries) == 2


@pytest.mark.parametrize(
    "mutation",
    [
        lambda snapshot: setattr(snapshot, "state", RunState.BLOCKED),
        lambda snapshot: setattr(snapshot, "delivery_approved", False),
        lambda snapshot: setattr(snapshot, "spec", None),
        lambda snapshot: setattr(snapshot, "feedback", None),
        lambda snapshot: setattr(snapshot, "proof", None),
        lambda snapshot: setattr(snapshot.proof, "publish_allowed", False),
        lambda snapshot: setattr(snapshot.proof, "verdict", Verdict.FAIL),
        lambda snapshot: setattr(snapshot.proof, "spec_hash", "wrong-spec"),
        lambda snapshot: snapshot.proof.checks.pop(),
        lambda snapshot: setattr(snapshot.proof.checks[0], "verdict", Verdict.ERROR),
        lambda snapshot: snapshot.proof.checks.append(snapshot.proof.checks[0]),
    ],
)
def test_save_requires_exact_three_pass_checks_and_final_human_approval(mutation) -> None:
    snapshot = ready_snapshot()
    mutation(snapshot)
    with pytest.raises(ValueError, match="all checks PASS"):
        manager().save(snapshot, None)
    assert snapshot.memory_saved is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda snapshot: setattr(snapshot, "change_map", None),
        lambda snapshot: setattr(snapshot.change_map, "status", "unavailable"),
        lambda snapshot: setattr(snapshot.change_map, "spec_hash", "wrong-spec"),
        lambda snapshot: setattr(snapshot.change_map, "version_label", "v2"),
        lambda snapshot: setattr(snapshot.change_map.windows[0], "status", "review"),
        lambda snapshot: snapshot.change_map.windows.clear(),
    ],
)
def test_save_requires_matching_measured_change_map_without_review_flags(mutation) -> None:
    snapshot = ready_snapshot()
    mutation(snapshot)
    with pytest.raises(ValueError, match="Change Map"):
        manager().save(snapshot, None)
    assert snapshot.memory_saved is False


@pytest.mark.parametrize("key", [None, "", "wrong-workspace-key", "한글키" * 8])
def test_live_save_requires_private_key_before_external_work(monkeypatch, key) -> None:
    intelligence = manager(live=True)
    writer = Mock(side_effect=AssertionError("unauthorized saves must not write"))
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", writer)
    with pytest.raises(PermissionError, match="private workspace key"):
        intelligence.save(ready_snapshot(), key)
    writer.assert_not_called()


def test_live_save_without_configured_key_is_read_only_even_if_caller_supplies_key() -> None:
    with pytest.raises(PermissionError):
        manager(live=True, memory_write_token=None).save(ready_snapshot(), PRIVATE_KEY)


def test_live_save_inserts_once_confirms_and_strips_evidence_urls(monkeypatch) -> None:
    intelligence = manager(live=True)
    snapshot = ready_snapshot()
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    queries = install_reader(monkeypatch, [[{"total": 0}], [{"total": 1}]])
    writer = Mock()
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: writer)
    saved = intelligence.save(snapshot, PRIVATE_KEY)
    assert saved.status == "saved"
    assert snapshot.memory_saved is True
    assert len(queries) == 2
    assert queries[0] == queries[1]
    row = writer.insert_approved_edit.call_args.args[0]
    assert row[0] == intelligence.settings.memory_workspace
    assert row[1] == saved.memory_id
    assert row[2] == snapshot.run_id
    assert row[9] == intelligence.settings.embedding_model
    stored_proof = json.loads(row[11])
    assert all(check["evidence_urls"] == [] for check in stored_proof["checks"])
    assert all(check.evidence_urls for check in snapshot.proof.checks)
    assert intelligence.save(snapshot, PRIVATE_KEY).status == "already_saved"
    writer.insert_approved_edit.assert_called_once()


def test_live_preexisting_identity_does_not_insert_again(monkeypatch) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    install_reader(monkeypatch, [[{"total": 1}]])
    writer = Mock()
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: writer)
    snapshot = ready_snapshot()
    intelligence.save(snapshot, PRIVATE_KEY)
    assert snapshot.memory_saved is True
    writer.insert_approved_edit.assert_not_called()


@pytest.mark.parametrize(
    "count",
    [
        [],
        [{"total": -1}],
        [{"total": 2}],
        [{"total": 1}, {"total": 0}],
        [{"total": 0.5}],
        [{"total": True}],
        [{"total": "not-an-integer"}],
    ],
)
def test_live_save_rejects_malformed_existing_count_before_writing(monkeypatch, count) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    queries = install_reader(monkeypatch, [count, [{"total": 1}]])
    writer = Mock()
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: writer)
    snapshot = ready_snapshot()
    with pytest.raises(RuntimeError, match="count|persistence"):
        intelligence.save(snapshot, PRIVATE_KEY)
    assert snapshot.memory_saved is False
    writer.insert_approved_edit.assert_not_called()
    assert len(queries) == 1


@pytest.mark.parametrize(
    "confirmation",
    [[], [{"total": 0}], [{"total": 2}], [{"total": 1.5}], [{"total": True}], [{"total": 1}] * 2],
)
def test_live_save_unconfirmed_write_does_not_mark_saved(monkeypatch, confirmation) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(intelligence, "_embedding", lambda _snapshot: UNIT_VECTOR)
    install_reader(monkeypatch, [[{"total": 0}], confirmation])
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: Mock())
    snapshot = ready_snapshot()
    with pytest.raises(RuntimeError, match="persistence|count"):
        intelligence.save(snapshot, PRIVATE_KEY)
    assert snapshot.memory_saved is False


def test_api_rejects_unknown_engine_and_unauthorized_live_save(runtime_dir: Path) -> None:
    settings = manager(live=True).settings
    settings.runtime_dir = runtime_dir
    repository = InMemoryRunRepository()
    snapshot = ready_snapshot()
    snapshot.mode = ExecutionMode.LIVE
    repository.create(snapshot, runtime_dir / "demo/revisionproof_v1.mp4")
    service = RevisionProofService(settings, repository)
    app = FastAPI()
    app.state.service = service
    app.include_router(router)
    client = TestClient(app)
    route = f"/api/runs/{snapshot.run_id}/edit-memory"
    assert client.get(route, params={"engine": "sql-injection"}).status_code == 422
    response = client.post(route)
    assert response.status_code == 403
    assert "private workspace key" in response.json()["detail"]
    assert snapshot.memory_saved is False
    assert snapshot.delivery_approved is True


def test_service_offline_mode_rejects_save_before_rehearsal_write(runtime_dir: Path) -> None:
    intelligence = manager(mode=ExecutionMode.OFFLINE_REHEARSAL, runtime_dir=runtime_dir)
    service = RevisionProofService(intelligence.settings, InMemoryRunRepository())
    with pytest.raises(ValueError, match="read-only"):
        service.save_memory(ready_snapshot().run_id)


@pytest.mark.asyncio
async def test_fixture_full_video_workflow_populates_map_and_human_approved_memory(
    runtime_dir: Path,
) -> None:
    settings = manager(runtime_dir=runtime_dir).settings
    service = RevisionProofService(settings, InMemoryRunRepository())
    request = CreateRunRequest(
        asset_id=DEMO_ASSET_ID,
        feedback='Apply a 6-second center PUNCH_IN when the presenter says "RevisionProof."',
    )
    snapshot = await service.create_run(request)
    assert snapshot.edit_memory is None  # optional lookup no longer blocks request review
    assert service.search_memory(snapshot.run_id, "exact").status == "empty"
    service.generate_previews(snapshot.run_id)
    service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    snapshot = service.render_approved_version(snapshot.run_id)
    assert snapshot.state is RunState.READY
    assert snapshot.proof is not None and snapshot.proof.publish_allowed
    assert snapshot.change_map is not None and snapshot.change_map.status == "ready"
    assert snapshot.change_map.source == "fixture.frame_analysis"
    assert len(snapshot.change_map.windows) == 30
    assert not any(window.status == "review" for window in snapshot.change_map.windows)
    assert not snapshot.delivery_approved
    with pytest.raises(ValueError, match="final human delivery approval"):
        service.save_memory(snapshot.run_id)

    # Fixture-only operator action: no LIVE delivery approval or external writes.
    service.approve_for_delivery(snapshot.run_id)
    result = service.save_memory(snapshot.run_id)
    assert result.status == "saved"
    assert snapshot.memory_saved
    assert service.save_memory(snapshot.run_id).status == "already_saved"
    later = await service.create_run(request)
    assert later.edit_memory is None
    assert service.search_memory(later.run_id, "exact").status == "ready"
    assert later.edit_memory is not None
    assert later.edit_memory.matches[0].memory_id == result.memory_id
    assert later.spec is None
    assert not later.delivery_approved
    assert not later.memory_saved
