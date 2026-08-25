from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from revisionproof.media.executor import MediaExecutor


class MediaInfo(BaseModel):
    duration_seconds: float
    width: int
    height: int
    video_codec: str
    audio_codec: str | None
    format_name: str


def probe_media(path: Path, executor: MediaExecutor) -> MediaInfo:
    raw = executor.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name:stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ]
    )
    data = json.loads(raw)
    video = next((stream for stream in data["streams"] if stream["codec_type"] == "video"), None)
    audio = next((stream for stream in data["streams"] if stream["codec_type"] == "audio"), None)
    if video is None:
        raise ValueError("upload has no video stream")
    return MediaInfo(
        duration_seconds=float(data["format"]["duration"]),
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        video_codec=video["codec_name"],
        audio_codec=audio["codec_name"] if audio else None,
        format_name=data["format"]["format_name"],
    )


def validate_hackathon_media(info: MediaInfo, *, max_duration_seconds: int) -> None:
    errors: list[str] = []
    if info.duration_seconds > max_duration_seconds:
        errors.append(f"duration exceeds {max_duration_seconds}s")
    if (info.width, info.height) != (1280, 720):
        errors.append("video must be 1280x720")
    if info.video_codec != "h264":
        errors.append("video codec must be H.264")
    if info.audio_codec != "aac":
        errors.append("audio codec must be AAC")
    if "mp4" not in info.format_name:
        errors.append("container must be MP4")
    if errors:
        raise ValueError("; ".join(errors))
