from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from revisionproof.contracts import (
    EvidenceAnchor,
    ParsedFeedback,
    RevisionNote,
    SafetyClassification,
    TimeRange,
)
from revisionproof.ids import new_ulid
from revisionproof.settings import Settings

_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def _normalize_note(text: str) -> str:
    without_marker = re.sub(r"^\s*(?:\d+[.)]|[-*])\s+", "", text)
    return re.sub(r"\s+", " ", without_marker).strip().casefold()


def _split_source_notes(raw_text: str) -> list[str]:
    markers = list(re.finditer(r"(?m)^\s*(?:\d+[.)]|[-*])\s+", raw_text))
    if markers:
        return [
            raw_text[
                marker.end() : markers[index + 1].start() if index + 1 < len(markers) else None
            ]
            for index, marker in enumerate(markers)
        ]
    lines = [line for line in raw_text.splitlines() if line.strip()]
    return lines or [raw_text]


def validate_interpretation_grounding(raw_text: str, notes: list[RevisionNote]) -> None:
    expected_notes = Counter(_normalize_note(item) for item in _split_source_notes(raw_text))
    returned_notes = Counter(_normalize_note(note.raw_text) for note in notes)
    if not expected_notes or "" in expected_notes or returned_notes != expected_notes:
        raise RuntimeError("Gemini notes do not exactly cover the client feedback")
    for note in notes:
        normalized_note = _normalize_note(note.raw_text)
        if note.target_phrase:
            normalized_target = _normalize_note(note.target_phrase)
            if normalized_target not in normalized_note:
                raise RuntimeError("Gemini returned a target phrase absent from its source note")


def decode_clickhouse_result(payload: Any) -> list[dict[str, Any]]:
    """Normalize the response shapes emitted by supported mcp-clickhouse releases."""
    if isinstance(payload, str):
        try:
            return decode_clickhouse_result(json.loads(payload))
        except json.JSONDecodeError as exc:
            raise RuntimeError("mcp-clickhouse returned invalid JSON") from exc
    if isinstance(payload, list):
        if all(isinstance(row, dict) for row in payload):
            return payload
        raise RuntimeError("mcp-clickhouse returned an unsupported row list")
    if isinstance(payload, dict):
        if "result" in payload:
            return decode_clickhouse_result(payload["result"])
        if isinstance(payload.get("data"), list):
            return decode_clickhouse_result(payload["data"])
        columns = payload.get("columns")
        rows = payload.get("rows")
        if isinstance(columns, list) and isinstance(rows, list):
            if not all(isinstance(column, str) for column in columns):
                raise RuntimeError("mcp-clickhouse returned invalid column names")
            normalized: list[dict[str, Any]] = []
            for row in rows:
                if not isinstance(row, list) or len(row) != len(columns):
                    raise RuntimeError("mcp-clickhouse returned a malformed row")
                normalized.append(dict(zip(columns, row, strict=True)))
            return normalized
    raise RuntimeError("mcp-clickhouse returned an unsupported response shape")


def build_segment_search_query(asset_id: str, embedding: list[float], limit: int = 5) -> str:
    if not _ULID_RE.fullmatch(asset_id):
        raise ValueError("asset_id must be a ULID")
    if len(embedding) != 768:
        raise ValueError("embedding must contain exactly 768 dimensions")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    vector = ",".join(format(float(value), ".9g") for value in embedding)
    return (
        "SELECT segment_id, start_seconds, end_seconds, transcript, visual_summary, "
        f"1 - cosineDistance(embedding, [{vector}]) AS score "
        "FROM search_segments "
        f"WHERE asset_id = '{asset_id}' ORDER BY score DESC LIMIT {limit}"
    )


def build_version_diff_query(run_id: str, current_version: str, baseline_version: str) -> str:
    if not _ULID_RE.fullmatch(run_id):
        raise ValueError("run_id must be a ULID")
    for value in (current_version, baseline_version):
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", value):
            raise ValueError("version label contains invalid characters")
    return (
        "SELECT feature_name, baseline_value, current_value, absolute_delta "
        "FROM version_feature_diff "
        f"WHERE run_id = '{run_id}' AND current_version = '{current_version}' "
        f"AND baseline_version = '{baseline_version}' ORDER BY feature_name"
    )


@dataclass(slots=True)
class McpClickHouseReader:
    settings: Settings

    async def run_query(self, query: str) -> list[dict[str, Any]]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise RuntimeError("install the backend 'live' extra to use ClickHouse MCP") from exc

        executable_name = "mcp-clickhouse.exe" if sys.platform == "win32" else "mcp-clickhouse"
        executable = str(Path(sys.executable).parent / executable_name)
        server = StdioServerParameters(
            command=executable,
            args=[],
            env={
                "PATH": os.environ.get("PATH", ""),
                "CLICKHOUSE_HOST": str(self.settings.clickhouse_host),
                "CLICKHOUSE_PORT": str(self.settings.clickhouse_port),
                "CLICKHOUSE_USER": self.settings.clickhouse_mcp_username,
                "CLICKHOUSE_PASSWORD": str(self.settings.clickhouse_mcp_password),
                "CLICKHOUSE_DATABASE": self.settings.clickhouse_database,
                "CLICKHOUSE_ROLE": self.settings.clickhouse_mcp_role,
                "CLICKHOUSE_SECURE": str(self.settings.clickhouse_secure).lower(),
                "CLICKHOUSE_VERIFY": str(self.settings.clickhouse_verify).lower(),
                "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
            },
        )
        async with asyncio.timeout(self.settings.mcp_timeout_seconds):
            async with (
                stdio_client(server) as (reader, writer),
                ClientSession(reader, writer) as session,
            ):
                await session.initialize()
                result = await session.call_tool("run_query", {"query": query})
        if result.isError:
            raise RuntimeError("mcp-clickhouse run_query returned an error")
        if result.structuredContent:
            return decode_clickhouse_result(result.structuredContent)
        text = "".join(getattr(item, "text", "") for item in result.content)
        return decode_clickhouse_result(text)


@dataclass(slots=True)
class VertexGeminiInterpreter:
    settings: Settings

    async def interpret_many(self, raw_text: str) -> list[RevisionNote]:
        try:
            from google.adk.agents import LlmAgent
            from google.adk.runners import InMemoryRunner
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("install the backend 'live' extra to use Google ADK") from exc

        class NoteOutput(BaseModel):
            raw_text: str = Field(min_length=1, max_length=2000)
            intent: str = Field(min_length=1, max_length=500)
            classification: SafetyClassification
            confidence: float = Field(ge=0, le=1)
            target_phrase: str | None = Field(default=None, max_length=200)
            rationale: str = Field(min_length=1, max_length=1000)
            clarification_question: str | None = Field(default=None, max_length=500)

        class InterpretationOutput(BaseModel):
            notes: list[NoteOutput] = Field(min_length=1, max_length=20)

        agent = LlmAgent(
            name="revision_note_interpreter",
            model=self.settings.gemini_model,
            instruction=(
                "Split the input into video revision notes and classify each one. "
                "AUTO_PREVIEWABLE is only a short 4-8 second center PUNCH_IN with a precise "
                "target phrase and confidence >= 0.82. NEEDS_CLARIFICATION is potentially "
                "supported but lacks a precise target or has confidence 0.55-0.82; ask one "
                "clarifying question. MANUAL_CREATIVE covers B-roll, restructuring, speed ramps, "
                "or other unsupported creation. Never approve or verify a revision."
                " Return one output note for every input list item or non-empty line. Preserve "
                "each note's raw_text verbatim, excluding only a leading list marker. Never merge, "
                "duplicate, or invent notes. A target_phrase must be a verbatim substring of that "
                "same note."
            ),
            output_schema=InterpretationOutput,
        )
        runner = InMemoryRunner(app_name="revisionproof", agent=agent)
        user_id = "revisionproof-api"
        session = await runner.session_service.create_session(
            app_name="revisionproof", user_id=user_id, session_id=new_ulid()
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=raw_text)])
        final_text = ""
        try:
            async with asyncio.timeout(self.settings.gemini_timeout_seconds):
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session.id,
                    new_message=content,
                ):
                    if event.content and event.content.parts:
                        texts = [part.text for part in event.content.parts if part.text]
                        if texts:
                            final_text = "\n".join(texts)
        finally:
            await runner.close()
        if not final_text:
            raise RuntimeError("Google ADK returned no interpretation")
        data = InterpretationOutput.model_validate_json(final_text)
        notes = [
            RevisionNote(
                note_id=f"note_{index:02d}",
                **note.model_dump(),
            )
            for index, note in enumerate(data.notes, start=1)
        ]
        validate_interpretation_grounding(raw_text, notes)
        return notes

    async def interpret(self, raw_text: str) -> ParsedFeedback:
        notes = await self.interpret_many(raw_text)
        note = next(
            (
                item
                for item in notes
                if item.classification is SafetyClassification.AUTO_PREVIEWABLE
            ),
            None,
        )
        if note is None or note.target_phrase is None:
            raise ValueError("feedback has no AUTO_PREVIEWABLE note")
        return ParsedFeedback(
            raw_text=note.raw_text,
            intent=note.intent,
            target_phrase=note.target_phrase,
            rationale=note.rationale,
            interpreter_source="google.vertex.gemini",
        )

    def embed(self, text: str) -> list[float]:
        from google import genai

        client = genai.Client(
            vertexai=True,
            project=self.settings.google_cloud_project,
            location=self.settings.google_cloud_location,
        )
        response = client.models.embed_content(model=self.settings.embedding_model, contents=text)
        values = list(response.embeddings[0].values)
        if len(values) != 768:
            raise RuntimeError(f"expected 768 embedding dimensions, got {len(values)}")
        return values


@dataclass(slots=True)
class ClickHouseWriter:
    settings: Settings

    def _client(self):
        try:
            import clickhouse_connect
        except ImportError as exc:
            raise RuntimeError("install the backend 'live' extra to write ClickHouse") from exc
        return clickhouse_connect.get_client(
            host=self.settings.clickhouse_host,
            port=self.settings.clickhouse_port,
            username=self.settings.clickhouse_writer_username,
            password=self.settings.clickhouse_writer_password,
            database=self.settings.clickhouse_database,
            secure=self.settings.clickhouse_secure,
            verify=self.settings.clickhouse_verify,
            settings={"role": self.settings.clickhouse_writer_role},
        )

    def insert_features(self, rows: list[list[Any]]) -> None:
        client = self._client()
        try:
            client.insert(
                "version_features",
                rows,
                column_names=[
                    "run_id",
                    "version_label",
                    "feature_name",
                    "feature_value",
                    "time_start",
                    "time_end",
                    "extracted_at",
                ],
            )
        finally:
            client.close()

    def insert_checks(self, rows: list[list[Any]]) -> None:
        client = self._client()
        try:
            client.insert(
                "version_checks",
                rows,
                column_names=[
                    "run_id",
                    "version_label",
                    "check_id",
                    "verdict",
                    "failure_code",
                    "measured_json",
                    "threshold_json",
                    "checked_at",
                ],
            )
        finally:
            client.close()

    def insert_spec(self, row: list[Any]) -> None:
        client = self._client()
        try:
            client.insert(
                "revision_specs",
                [row],
                column_names=["run_id", "spec_hash", "canonical_json", "approved_at"],
            )
        finally:
            client.close()


@dataclass(slots=True)
class GcsObjectStore:
    settings: Settings

    def upload(self, local_path, object_name: str) -> str:
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("install the backend 'live' extra to use GCS") from exc
        client = storage.Client(project=self.settings.google_cloud_project)
        bucket = client.bucket(str(self.settings.gcs_bucket))
        blob = bucket.blob(object_name)
        blob.upload_from_filename(str(local_path), content_type="video/mp4")
        return f"gs://{self.settings.gcs_bucket}/{object_name}"


@dataclass(slots=True)
class LiveEvidenceLocator:
    settings: Settings
    reader: McpClickHouseReader
    interpreter: VertexGeminiInterpreter

    async def locate(self, asset_id: str, feedback: ParsedFeedback) -> list[EvidenceAnchor]:
        async with asyncio.timeout(self.settings.gemini_timeout_seconds):
            embedding = await asyncio.to_thread(self.interpreter.embed, feedback.target_phrase)
        rows = await self.reader.run_query(build_segment_search_query(asset_id, embedding, 5))
        anchors = [
            EvidenceAnchor(
                segment_id=str(row["segment_id"]),
                time_range=TimeRange(
                    start_seconds=float(row["start_seconds"]),
                    end_seconds=float(row["end_seconds"]),
                ),
                score=float(row["score"]),
                transcript=str(row["transcript"]),
                visual_summary=str(row["visual_summary"]),
                source="mcp-clickhouse.run_query",
            )
            for row in rows[:3]
        ]
        if not anchors:
            raise RuntimeError("mcp-clickhouse evidence search returned no rows")
        return anchors
