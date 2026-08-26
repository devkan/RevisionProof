from __future__ import annotations

from pathlib import Path

import pytest

import revisionproof.evidence.live as live_adapters
from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    EvidenceAnchor,
    ExecutionMode,
    RevisionNote,
    RunSnapshot,
    RunState,
    SafetyClassification,
    TimeRange,
)
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings


def _snapshot() -> RunSnapshot:
    return RunSnapshot(
        run_id="01J00000000000000000000077",
        asset={
            "asset_id": DEMO_ASSET_ID,
            "title": "RevisionProof — Product Reveal",
            "source_url": "/media/demo/revisionproof_v1.mp4",
            "duration_seconds": 30,
            "width": 1280,
            "height": 720,
            "codec": "h264",
        },
        mode=ExecutionMode.LIVE,
        state=RunState.INDEXED,
        source_feedback='When the presenter says "RevisionProof," push in slightly.',
    )


def _settings(runtime_dir: Path) -> Settings:
    return Settings(
        mode=ExecutionMode.LIVE,
        runtime_dir=runtime_dir,
        google_cloud_project="revisionproof-test",
        gcs_bucket="revisionproof-test-media",
        clickhouse_host="example.clickhouse.cloud",
        clickhouse_writer_password="writer",
        clickhouse_mcp_password="reader",
    )


def _install_fake_live_path(monkeypatch, score: float) -> None:
    class FakeInterpreter:
        def __init__(self, settings) -> None:
            assert settings.google_cloud_project == "revisionproof-test"

        async def interpret_many(self, raw_text: str):
            return [
                RevisionNote(
                    note_id="note_01",
                    raw_text=raw_text,
                    intent="Apply a short center punch-in on the named reveal",
                    classification=SafetyClassification.AUTO_PREVIEWABLE,
                    confidence=0.94,
                    target_phrase="RevisionProof",
                    rationale="The target phrase and supported edit are precise.",
                )
            ]

    class FakeReader:
        def __init__(self, settings) -> None:
            assert settings.clickhouse_mcp_username == "revisionproof_mcp_user"

    class FakeLocator:
        def __init__(self, settings, reader, interpreter) -> None:
            assert isinstance(reader, FakeReader)
            assert isinstance(interpreter, FakeInterpreter)

        async def locate(self, asset_id, feedback):
            assert asset_id == DEMO_ASSET_ID
            assert feedback.interpreter_source == "google.vertex.gemini"
            return [
                EvidenceAnchor(
                    segment_id="01J00000000000000000000002",
                    time_range=TimeRange(start_seconds=8, end_seconds=14),
                    score=score,
                    transcript='The presenter says "RevisionProof".',
                    visual_summary="The product reveal fills the center frame.",
                    source="mcp-clickhouse.run_query",
                )
            ]

    monkeypatch.setattr(live_adapters, "VertexGeminiInterpreter", FakeInterpreter)
    monkeypatch.setattr(live_adapters, "McpClickHouseReader", FakeReader)
    monkeypatch.setattr(live_adapters, "LiveEvidenceLocator", FakeLocator)


@pytest.mark.asyncio
async def test_live_interpretation_uses_vertex_and_official_mcp_adapters(
    runtime_dir: Path, monkeypatch
) -> None:
    _install_fake_live_path(monkeypatch, score=0.93)
    repository = InMemoryRunRepository()
    snapshot = _snapshot()
    repository.create(snapshot, runtime_dir / "demo" / "revisionproof_v1.mp4")
    service = RevisionProofService(_settings(runtime_dir), repository)

    await service._run_live_interpretation(snapshot, snapshot.source_feedback or "")  # noqa: SLF001

    assert snapshot.state is RunState.EVIDENCE_ANCHORED
    assert snapshot.feedback is not None
    assert snapshot.feedback.interpreter_source == "google.vertex.gemini"
    assert snapshot.evidence[0].source == "mcp-clickhouse.run_query"
    assert [event.state for event in snapshot.events] == [
        RunState.INDEXED,
        RunState.NOTES_PARSED,
        RunState.EVIDENCE_ANCHORED,
    ]


@pytest.mark.asyncio
async def test_live_interpretation_holds_low_score_evidence_for_clarification(
    runtime_dir: Path, monkeypatch
) -> None:
    _install_fake_live_path(monkeypatch, score=0.70)
    repository = InMemoryRunRepository()
    snapshot = _snapshot()
    repository.create(snapshot, runtime_dir / "demo" / "revisionproof_v1.mp4")
    service = RevisionProofService(_settings(runtime_dir), repository)

    await service._run_live_interpretation(snapshot, snapshot.source_feedback or "")  # noqa: SLF001

    assert snapshot.state is RunState.NOTES_PARSED
    assert snapshot.feedback is None
    assert snapshot.evidence == []
    assert snapshot.notes[0].classification is SafetyClassification.NEEDS_CLARIFICATION
    assert snapshot.notes[0].confidence == 0.70
    assert "below 0.82" in snapshot.events[-1].message
