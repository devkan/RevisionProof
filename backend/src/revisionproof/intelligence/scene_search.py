"""Opt-in scene indexing and ClickHouse-backed semantic search."""

from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import cv2
from pydantic import BaseModel, Field

from revisionproof.evidence.live import (
    ClickHouseWriter,
    McpClickHouseReader,
    VertexGeminiInterpreter,
    normalize_clickhouse_fixed_string,
)
from revisionproof.ids import new_ulid
from revisionproof.intelligence.models import SceneSearchHit, SceneSearchResult
from revisionproof.intelligence.queries import build_smart_scene_search_query, normalize_embedding


class FrameDescription(BaseModel):
    frame_index: int = Field(ge=0, le=14)
    visual_summary: str = Field(min_length=1, max_length=600)
    visible_text: str = Field(default="", max_length=300)


class FrameDescriptions(BaseModel):
    frames: list[FrameDescription] = Field(min_length=1, max_length=15)


def _sample_frames(source: Path, duration: float) -> list[tuple[int, float, bytes]]:
    count = min(15, max(1, math.ceil(duration / 4)))
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError("The video could not be opened for scene search.")
    frames: list[tuple[int, float, bytes]] = []
    try:
        for index in range(count):
            second = min(duration - 0.05, index * 4 + min(2, duration / 2))
            capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
            ok, frame = capture.read()
            if not ok:
                continue
            height, width = frame.shape[:2]
            if width > 640:
                frame = cv2.resize(frame, (640, max(1, round(height * 640 / width))))
            encoded, payload = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 76])
            if encoded:
                frames.append((index, second, payload.tobytes()))
    finally:
        capture.release()
    if not frames:
        raise ValueError("No readable frames were found in this video.")
    return frames


async def _describe_frames(source: Path, duration: float, settings) -> list[dict]:
    from google import genai
    from google.genai import types

    frames = await asyncio.to_thread(_sample_frames, source, duration)
    contents = [
        types.Part.from_text(
            text=(
                "Describe each numbered video frame for later scene retrieval. Keep concrete "
                "objects, actions, layout, colors, and visible words. Do not infer unseen events, "
                "people, brands, or intent. Return exactly one item for every supplied frame_index."
            )
        )
    ]
    for index, second, payload in frames:
        contents.extend(
            [
                types.Part.from_text(text=f"frame_index={index}, time={second:.2f}s"),
                types.Part.from_bytes(data=payload, mime_type="image/jpeg"),
            ]
        )
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    try:
        async with asyncio.timeout(settings.gemini_timeout_seconds):
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=FrameDescriptions,
                ),
            )
        parsed = (
            response.parsed
            if isinstance(response.parsed, FrameDescriptions)
            else FrameDescriptions.model_validate_json(response.text or "")
        )
    finally:
        await client.aio.aclose()
        client.close()
    by_index = {item.frame_index: item for item in parsed.frames}
    segments = []
    for index, _second, _payload in frames:
        item = by_index.get(index)
        if item is None:
            raise ValueError("AI scene descriptions did not cover every sampled frame.")
        start = index * 4.0
        end = min(duration, start + 4.0)
        segments.append(
            {
                "segment_id": new_ulid(),
                "start_seconds": start,
                "end_seconds": end,
                "transcript": item.visible_text.strip(),
                "visual_summary": item.visual_summary.strip(),
            }
        )
    return segments


async def search_live_scenes(
    source: Path, *, duration: float, query: str, asset_id: str, settings
) -> SceneSearchResult:
    segments = await _describe_frames(source, duration, settings)
    texts = [f"{item['visual_summary']}\n{item['transcript']}" for item in segments]
    interpreter = VertexGeminiInterpreter(settings)
    vectors = await asyncio.to_thread(interpreter.embed_many, [*texts, query])
    created_at = datetime.now(UTC)
    search_id = new_ulid()
    rows = [
        [
            settings.memory_workspace,
            search_id,
            item["segment_id"],
            asset_id,
            item["start_seconds"],
            item["end_seconds"],
            item["transcript"],
            item["visual_summary"],
            normalize_embedding(vector),
            created_at,
            created_at + timedelta(days=7),
        ]
        for item, vector in zip(segments, vectors[:-1], strict=True)
    ]
    await asyncio.to_thread(ClickHouseWriter(settings).insert_smart_segments, rows)
    rows = await McpClickHouseReader(settings).run_query(
        build_smart_scene_search_query(
            settings.memory_workspace,
            search_id,
            asset_id,
            normalize_embedding(vectors[-1]),
            3,
        )
    )
    hits = []
    for row in rows:
        score = float(row["score"])
        if not math.isfinite(score):
            raise ValueError("ClickHouse returned an invalid scene score.")
        hits.append(
            SceneSearchHit(
                segment_id=normalize_clickhouse_fixed_string(row["segment_id"]),
                start_seconds=float(row["start_seconds"]),
                end_seconds=float(row["end_seconds"]),
                score=max(-1, min(1, score)),
                transcript=str(row["transcript"]),
                visual_summary=str(row["visual_summary"]),
            )
        )
    return SceneSearchResult(
        search_id=search_id,
        asset_id=asset_id,
        query=query,
        source="mcp-clickhouse.run_query",
        segments_indexed=len(segments),
        matches=hits,
        message="AI described sampled frames; ClickHouse ranked the indexed scene segments.",
    )


def search_fixture_scenes(duration: float, query: str, asset_id: str) -> SceneSearchResult:
    count = min(15, max(1, math.ceil(duration / 4)))
    hits = [
        SceneSearchHit(
            segment_id=new_ulid(),
            start_seconds=index * 4,
            end_seconds=min(duration, index * 4 + 4),
            score=max(0.55, 0.92 - index * 0.08),
            visual_summary=f"Local rehearsal scene {index + 1}; no live visual claim.",
        )
        for index in range(min(3, count))
    ]
    return SceneSearchResult(
        search_id=new_ulid(),
        asset_id=asset_id,
        query=query,
        source="fixture.scene_search",
        segments_indexed=count,
        matches=hits,
        message="Local fixture results; no Google or ClickHouse credits were used.",
    )
