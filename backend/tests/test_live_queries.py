import pytest

from revisionproof.evidence.live import (
    McpClickHouseReader,
    build_segment_search_query,
    build_version_diff_query,
    decode_clickhouse_result,
    normalize_clickhouse_fixed_string,
)
from revisionproof.settings import Settings

ULID = "01J00000000000000000000000"


def test_segment_query_targets_read_view_and_uses_768_vector() -> None:
    query = build_segment_search_query(ULID, [0.0] * 768)
    assert "FROM search_segments" in query
    assert "cosineDistance" in query
    assert "LIMIT 5" in query


def test_segment_query_rejects_user_sql_and_wrong_dimensions() -> None:
    with pytest.raises(ValueError):
        build_segment_search_query("x' OR 1=1 --", [0.0] * 768)
    with pytest.raises(ValueError):
        build_segment_search_query(ULID, [0.0] * 767)


def test_version_diff_query_targets_read_view() -> None:
    query = build_version_diff_query(ULID, "v3", "v1")
    assert "FROM version_feature_diff" in query
    assert "current_version = 'v3'" in query


def test_mcp_clickhouse_result_decoder_supports_current_envelope() -> None:
    payload = {"result": '{"columns":["transcript","dimensions"],"rows":[["proof",768]]}'}
    assert decode_clickhouse_result(payload) == [{"transcript": "proof", "dimensions": 768}]


def test_mcp_clickhouse_result_decoder_rejects_malformed_rows() -> None:
    with pytest.raises(RuntimeError, match="malformed row"):
        decode_clickhouse_result({"columns": ["one", "two"], "rows": [[1]]})


def test_clickhouse_fixed_string_normalizer_supports_mcp_encodings() -> None:
    segment_id = "01J00000000000000000000002"

    assert normalize_clickhouse_fixed_string(segment_id) == segment_id
    assert normalize_clickhouse_fixed_string(segment_id.encode()) == segment_id
    assert normalize_clickhouse_fixed_string(f"b'{segment_id}\\x00'") == segment_id


@pytest.mark.asyncio
async def test_mcp_reader_retries_one_timeout(monkeypatch) -> None:
    calls = 0

    async def fake_run_once(_self, query: str):
        nonlocal calls
        assert query == "SELECT 1"
        calls += 1
        if calls == 1:
            raise TimeoutError
        return [{"1": 1}]

    monkeypatch.setattr(McpClickHouseReader, "_run_query_once", fake_run_once)

    rows = await McpClickHouseReader(Settings()).run_query("SELECT 1")

    assert rows == [{"1": 1}]
    assert calls == 2


@pytest.mark.asyncio
async def test_mcp_reader_propagates_second_timeout(monkeypatch) -> None:
    calls = 0

    async def fake_run_once(_self, _query: str):
        nonlocal calls
        calls += 1
        raise TimeoutError

    monkeypatch.setattr(McpClickHouseReader, "_run_query_once", fake_run_once)

    with pytest.raises(TimeoutError):
        await McpClickHouseReader(Settings()).run_query("SELECT 1")

    assert calls == 2
