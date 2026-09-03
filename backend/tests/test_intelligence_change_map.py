from pathlib import Path
from unittest.mock import Mock

import pytest
from test_contracts import make_spec
from test_intelligence_service import install_reader, manager, ready_snapshot

import revisionproof.intelligence.service as intelligence_module
from revisionproof.intelligence.change_map import (
    aggregate_fixture_pairs,
    classify_window,
    measure_frame_pairs,
)
from revisionproof.media.executor import MediaExecutor


def pair(sample_ms=250, **overrides) -> dict:
    result = {
        "sample_ms": sample_ms,
        "visual_delta": 0.1,
        "residual_delta": 0.01,
        "cta_delta": 0,
        "audio_delta_db": 0.1,
        "requested": 0,
    }
    result.update(overrides)
    return result


def test_aggregation_is_sorted_and_duplicate_retry_insensitive() -> None:
    first = pair(250)
    second = pair(750, requested=1, visual_delta=0.3)
    later = pair(2250, residual_delta=0.05)
    result = aggregate_fixture_pairs([later, second, first, first, second, later])
    assert [window.second for window in result] == [0, 2]
    assert [window.sample_count for window in result] == [2, 1]
    assert result[0].visual_delta == 0.3
    assert result[0].requested is True
    assert result[0].status == "requested"
    assert result[1].status == "review"


@pytest.mark.parametrize(
    "field,value",
    [("residual_delta", 0.036), ("cta_delta", 0.061), ("audio_delta_db", 3.01)],
)
def test_any_unexpected_change_becomes_review_even_inside_requested_patch(field, value) -> None:
    row = {**pair(requested=1), "second": 8, "sample_count": 2, field: value}
    assert classify_window(row).status == "review"


def test_exact_thresholds_are_not_review_and_color_does_not_define_status() -> None:
    row = {
        **pair(),
        "second": 0,
        "sample_count": 2,
        "residual_delta": 0.035,
        "cta_delta": 0.06,
        "audio_delta_db": 3.0,
    }
    assert classify_window(row).status == "unchanged"
    row["requested"] = 1
    assert classify_window(row).status == "requested"


@pytest.mark.parametrize("duration", [0, -1, 600.1])
def test_measurement_duration_is_bounded_before_media_execution(duration) -> None:
    executor = Mock()
    with pytest.raises(ValueError, match="duration"):
        measure_frame_pairs(
            Path("source.mp4"), Path("candidate.mp4"), make_spec(), duration, executor
        )
    executor.run.assert_not_called()


def test_fixture_map_uses_measured_frames_but_never_writes_clickhouse(monkeypatch) -> None:
    intelligence = manager()
    pairs = [pair(250), pair(750)]
    monkeypatch.setattr(intelligence_module, "measure_frame_pairs", lambda *_args: pairs)
    writer = Mock(side_effect=AssertionError("fixture map cannot write ClickHouse"))
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", writer)
    snapshot = ready_snapshot()
    result = intelligence.build_map(snapshot, Path("source"), Path("candidate"), Mock())
    assert result.status == "ready"
    assert result.source == "fixture.frame_analysis"
    assert result.windows == aggregate_fixture_pairs(pairs)
    assert result.spec_hash == snapshot.spec.spec_hash
    writer.assert_not_called()


def test_live_map_inserts_measurements_then_reads_aggregated_mcp_view(monkeypatch) -> None:
    intelligence = manager(live=True)
    pairs = [pair(250), pair(750)]
    monkeypatch.setattr(intelligence_module, "measure_frame_pairs", lambda *_args: pairs)
    writer = Mock()
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: writer)
    rows = [window.model_dump() for window in aggregate_fixture_pairs(pairs)]
    queries = install_reader(monkeypatch, [rows])
    snapshot = ready_snapshot()
    result = intelligence.build_map(snapshot, Path("source"), Path("candidate"), Mock())
    assert result.status == "ready"
    assert result.source == "mcp-clickhouse.run_query"
    assert len(result.windows) == 1
    inserted = writer.insert_frame_pairs.call_args.args[0]
    assert len(inserted) == 2
    assert all(row[0] == intelligence.settings.memory_workspace for row in inserted)
    assert all(row[1] == snapshot.run_id for row in inserted)
    assert all(row[4] == result.analysis_id for row in inserted)
    assert result.analysis_id in queries[0]
    assert "FROM revision_change_map" in queries[0]


@pytest.mark.parametrize(
    "stored",
    [[], [{**pair(), "second": 0, "sample_count": 1}], TimeoutError("MCP unavailable")],
)
def test_live_map_missing_mcp_coverage_fails_visible_without_fixture_fallback(
    monkeypatch, stored
) -> None:
    intelligence = manager(live=True)
    monkeypatch.setattr(
        intelligence_module, "measure_frame_pairs", lambda *_args: [pair(250), pair(750)]
    )
    monkeypatch.setattr(intelligence_module, "ClickHouseWriter", lambda _settings: Mock())
    install_reader(monkeypatch, [stored])
    snapshot = ready_snapshot()
    original_proof = snapshot.proof.model_dump()
    result = intelligence.build_map(snapshot, Path("source"), Path("candidate"), Mock())
    assert result.status == "unavailable"
    assert result.source == "mcp-clickhouse.run_query"
    assert result.windows == []
    assert snapshot.proof.model_dump() == original_proof


def test_measurement_failure_does_not_publish_partial_or_synthetic_map(monkeypatch) -> None:
    intelligence = manager()
    measurement = Mock(side_effect=ValueError("video does not decode"))
    monkeypatch.setattr(intelligence_module, "measure_frame_pairs", measurement)
    result = intelligence.build_map(ready_snapshot(), Path("source"), Path("candidate"), Mock())
    assert result.status == "unavailable"
    assert result.windows == []


@pytest.mark.parametrize("version,has_cta_flags", [("v3_ready", False), ("v2_blocked", True)])
def test_real_demo_media_map_marks_patch_and_detects_missing_cta(
    runtime_dir: Path, version: str, has_cta_flags: bool
) -> None:
    source = runtime_dir / "demo/revisionproof_v1.mp4"
    candidate = runtime_dir / f"demo/revisionproof_{version}.mp4"
    assert source.is_file() and candidate.is_file(), "Generate documented demo fixtures first"
    pairs = measure_frame_pairs(source, candidate, make_spec(), 30, MediaExecutor())
    windows = aggregate_fixture_pairs(pairs)
    assert len(pairs) == 60
    assert len(windows) == 30
    assert all(window.sample_count == 2 for window in windows)
    assert [window.second for window in windows if window.requested] == list(range(8, 14))
    cta_flags = [
        window for window in windows if 24 <= window.second < 29 and window.status == "review"
    ]
    assert bool(cta_flags) is has_cta_flags
    if not has_cta_flags:
        assert not [window for window in windows if window.status == "review"]
