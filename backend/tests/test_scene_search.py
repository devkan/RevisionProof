from __future__ import annotations

from pathlib import Path

import pytest

import revisionproof.intelligence.scene_search as scene_module
from revisionproof.contracts import ExecutionMode
from revisionproof.intelligence.scene_search import search_live_scenes
from revisionproof.settings import Settings


@pytest.mark.asyncio
async def test_live_scene_search_writes_expiring_scoped_rows_then_reads_through_mcp(
    monkeypatch,
) -> None:
    async def descriptions(_source, _duration, _settings):
        return [
            {
                "segment_id": "01M00000000000000000000003",
                "start_seconds": 4,
                "end_seconds": 8,
                "transcript": "KANAPP",
                "visual_summary": "A dashboard chart fills the screen.",
            }
        ]

    inserted = []
    queries = []

    class Interpreter:
        def __init__(self, _settings):
            pass

        def embed_many(self, texts):
            assert texts[-1] == "dashboard chart"
            return [[1.0] + [0.0] * 767 for _ in texts]

    class Writer:
        def __init__(self, _settings):
            pass

        def insert_smart_segments(self, rows):
            inserted.extend(rows)

    class Reader:
        def __init__(self, _settings):
            pass

        async def run_query(self, query):
            queries.append(query)
            return [
                {
                    "segment_id": "01M00000000000000000000003",
                    "start_seconds": 4,
                    "end_seconds": 8,
                    "transcript": "KANAPP",
                    "visual_summary": "A dashboard chart fills the screen.",
                    "score": 0.91,
                }
            ]

    monkeypatch.setattr(scene_module, "_describe_frames", descriptions)
    monkeypatch.setattr(scene_module, "VertexGeminiInterpreter", Interpreter)
    monkeypatch.setattr(scene_module, "ClickHouseWriter", Writer)
    monkeypatch.setattr(scene_module, "McpClickHouseReader", Reader)
    settings = Settings(
        _env_file=None,
        mode=ExecutionMode.LIVE,
        google_cloud_project="test-project",
        gcs_bucket="test-bucket",
        clickhouse_host="test.clickhouse.cloud",
        clickhouse_writer_password="writer",
        clickhouse_mcp_password="reader",
        intelligence_enabled=True,
    )
    result = await search_live_scenes(
        Path("unused.mp4"),
        duration=12,
        query="dashboard chart",
        asset_id="01M00000000000000000000002",
        settings=settings,
    )
    assert result.source == "mcp-clickhouse.run_query"
    assert result.matches[0].start_seconds == 4
    assert inserted[0][0] == "revisionproof-demo"
    assert inserted[0][1] == result.search_id
    assert (inserted[0][-1] - inserted[0][-2]).days == 7
    assert "FROM smart_scene_search" in queries[0]
    assert result.search_id in queries[0]
