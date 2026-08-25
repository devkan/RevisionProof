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
