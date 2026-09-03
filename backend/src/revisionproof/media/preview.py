from __future__ import annotations

from pathlib import Path

from revisionproof.contracts import PatchCandidate
from revisionproof.media.executor import MediaExecutor


def punch_in_filter(scale: float) -> str:
    crop_width = round(1280 / scale)
    crop_height = round(720 / scale)
    return (
        f"crop={crop_width}:{crop_height}:(iw-{crop_width})/2:(ih-{crop_height})/2,scale=1280:720"
    )


def generate_preview(
    *, source: Path, destination: Path, candidate: PatchCandidate, executor: MediaExecutor
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    duration = candidate.time_range.end_seconds - candidate.time_range.start_seconds
    executor.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{candidate.time_range.start_seconds:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-vf",
            punch_in_filter(candidate.scale),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        expected_output=destination,
    )
    return destination


def generate_full_revision(
    *, source: Path, destination: Path, candidate: PatchCandidate, executor: MediaExecutor
) -> Path:
    """Apply an approved punch-in to the source while preserving its full timeline."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    start = candidate.time_range.start_seconds
    end = candidate.time_range.end_seconds
    filter_graph = (
        f"[0:v]split=2[base][patch_in];"
        f"[patch_in]{punch_in_filter(candidate.scale)}[patch];"
        f"[base][patch]overlay=0:0:enable='gte(t,{start:.3f})*lt(t,{end:.3f})'[outv]"
    )
    executor.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            filter_graph,
            "-map",
            "[outv]",
            "-map",
            "0:a?",
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
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        expected_output=destination,
    )
    return destination
