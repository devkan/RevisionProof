from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

from revisionproof.media.executor import MediaExecutor


def read_frame(path: Path, seconds: float, *, frame_index: int | None = None) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    try:
        if frame_index is None:
            capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
        else:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
    finally:
        capture.release()
    if not ok or frame is None:
        raise ValueError(f"could not decode frame at {seconds:.3f}s")
    return frame


def write_frame_png(path: Path, seconds: float, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), read_frame(path, seconds)):
        raise ValueError(f"could not write evidence frame: {destination}")


def apply_punch_in(frame: np.ndarray, scale: float) -> np.ndarray:
    height, width = frame.shape[:2]
    crop_width = round(width / scale)
    crop_height = round(height / scale)
    x = (width - crop_width) // 2
    y = (height - crop_height) // 2
    cropped = frame[y : y + crop_height, x : x + crop_width]
    return cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)


def normalized_similarity(expected: np.ndarray, actual: np.ndarray) -> float:
    if expected.shape != actual.shape:
        actual = cv2.resize(actual, (expected.shape[1], expected.shape[0]))
    difference = cv2.absdiff(expected, actual)
    return float(max(0.0, 1.0 - np.mean(difference) / 255.0))


def roi_similarity(
    expected: np.ndarray, actual: np.ndarray, roi: tuple[int, int, int, int]
) -> float:
    x, y, width, height = roi
    expected_roi = expected[y : y + height, x : x + width]
    actual_roi = actual[y : y + height, x : x + width]
    return normalized_similarity(expected_roi, actual_roi)


def audio_levels_db(
    path: Path, *, start_seconds: float, duration_seconds: float, executor: MediaExecutor
) -> tuple[float, float]:
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f"{path.stem}-audio-", suffix=".f32le", dir=path.parent
    )
    os.close(descriptor)
    raw_path = Path(raw_name)
    raw_path.unlink()
    try:
        executor.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{start_seconds:.3f}",
                "-i",
                str(path),
                "-t",
                f"{duration_seconds:.3f}",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "48000",
                "-f",
                "f32le",
                str(raw_path),
            ],
            expected_output=raw_path,
        )
        samples = np.fromfile(raw_path, dtype=np.float32)
    finally:
        if raw_path.exists():
            raw_path.unlink()
    if samples.size == 0:
        raise ValueError("audio stream produced no samples")
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
    peak = float(np.max(np.abs(samples)))
    return 20 * math.log10(max(rms, 1e-12)), 20 * math.log10(max(peak, 1e-12))
