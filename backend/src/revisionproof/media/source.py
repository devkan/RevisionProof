"""Bounded source upload preparation; user-selected ranges never use the demo index."""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import BinaryIO

from revisionproof.contracts import RevisionNote, SafetyClassification, TimeRange
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import MediaInfo, probe_media, validate_hackathon_media
from revisionproof.settings import Settings


class SourceUploadError(ValueError):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def copy_source(stream: BinaryIO, destination: Path, limit: int, expected_hash: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_hash):
        raise SourceUploadError("The upload checksum is missing. Please select the video again.")
    digest = hashlib.sha256()
    total = 0
    with destination.open("xb") as output:
        while chunk := stream.read(min(1024 * 1024, limit - total + 1)):
            total += len(chunk)
            if total > limit:
                raise SourceUploadError(
                    f"Video is too large. Maximum: {limit // 1_000_000} MB.", 413
                )
            digest.update(chunk)
            output.write(chunk)
    if not total:
        raise SourceUploadError("This file is empty. Choose a video with content.")
    if digest.hexdigest() != expected_hash.lower():
        raise SourceUploadError("The video upload was incomplete. Please try again.")
    return digest.hexdigest()


def validate_source(info: MediaInfo, selected: TimeRange, settings: Settings) -> None:
    if (
        not math.isfinite(info.duration_seconds)
        or not 4 <= info.duration_seconds <= settings.max_duration_seconds
    ):
        raise SourceUploadError(
            f"Choose a video between 4 and {settings.max_duration_seconds} seconds long."
        )
    if not 4 <= selected.end_seconds - selected.start_seconds <= 8:
        raise SourceUploadError("Select a 4–8 second section to edit.")
    if selected.end_seconds > info.duration_seconds:
        raise SourceUploadError("The selected section extends beyond the end of this video.")
    if not (16 <= info.width <= 4096 and 16 <= info.height <= 4096):
        raise SourceUploadError("Video dimensions must be between 16 and 4096 pixels per side.")
    if info.video_codec not in {"h264", "hevc", "vp8", "vp9", "av1", "mpeg4"}:
        raise SourceUploadError(
            "This video codec is not supported. Export as H.264 MP4 and try again.", 415
        )
    if not any(name in info.format_name.split(",") for name in ("mp4", "mov", "webm", "matroska")):
        raise SourceUploadError("Choose an MP4, MOV, or WebM video.", 415)


def prepare_source(
    path: Path, destination: Path, selected: TimeRange, settings: Settings, executor: MediaExecutor
) -> MediaInfo:
    try:
        info = probe_media(path, executor)
    except Exception as exc:
        raise SourceUploadError(
            "This file could not be read as a video. Try exporting it as MP4."
        ) from exc
    validate_source(info, selected, settings)
    args = ["ffmpeg", "-y", "-i", str(path)]
    if info.audio_codec is None:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    args += [
        "-map",
        "0:v:0",
        "-map",
        "0:a:0" if info.audio_codec else "1:a:0",
        "-t",
        f"{info.duration_seconds:.6f}",
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-maxrate",
        "2400k",
        "-bufsize",
        "4800k",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-map_metadata",
        "-1",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    try:
        executor.run(args, expected_output=destination)
        prepared = probe_media(destination, executor)
        validate_hackathon_media(prepared, max_duration_seconds=settings.max_duration_seconds)
    except Exception as exc:
        raise SourceUploadError(
            "This video could not be prepared. Try a shorter clip exported as H.264 MP4."
        ) from exc
    if (
        selected.end_seconds > prepared.duration_seconds
        or abs(prepared.duration_seconds - info.duration_seconds) > 0.15
    ):
        raise SourceUploadError(
            "Video timing could not be preserved. Export a constant-frame-rate MP4 and retry."
        )
    if destination.stat().st_size > settings.max_upload_bytes:
        raise SourceUploadError(
            "Prepared video exceeds the size limit. Please upload a shorter clip.", 413
        )
    return prepared


def unsupported_edit_reason(text: str) -> str | None:
    """Only remove automation eligibility; never infer an executable partial edit."""
    lower = text.casefold()
    if any(
        word in lower
        for word in (
            "subtitle",
            "caption",
            "overlay",
            "watermark",
            "logo",
            "text",
            "title",
            "문구",
            "텍스트",
            "자막",
            "로고",
            "워터마크",
            "타이틀",
        )
    ):
        return (
            "Text, captions and logos cannot be added in this version. "
            "Edit your request to ask only for a center punch-in, "
            "or add the text in a video editor."
        )
    if any(
        word in lower
        for word in (
            "b-roll",
            "remove",
            "cut",
            "speed",
            "삭제",
            "속도",
            "색상",
        )
    ):
        return "This edit needs a video editor. This version only creates a center punch-in."
    return None


def interpret_selected_range(text: str) -> list[RevisionNote]:
    """Conservative local rehearsal rules; never claim speech or visual understanding."""
    notes = []
    for index, line in enumerate(filter(str.strip, text.splitlines()), 1):
        raw = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        lower = raw.casefold()
        supported = any(word in lower for word in ("punch", "zoom in", "확대", "줌인", "줌 인"))
        other = unsupported_edit_reason(raw)
        notes.append(
            RevisionNote(
                note_id=f"note_{index:02d}",
                raw_text=raw,
                intent="Apply a center punch-in to your selected section."
                if supported and not other
                else other
                or "This request needs an editor or a more specific supported instruction.",
                classification=SafetyClassification.AUTO_PREVIEWABLE
                if supported and not other
                else SafetyClassification.MANUAL_CREATIVE,
                confidence=1.0,
                target_phrase="user-selected section" if supported and not other else None,
                rationale=(
                    "Local rule match; timing comes from your explicit selection. "
                    "No transcript was inferred."
                ),
            )
        )
    return notes
