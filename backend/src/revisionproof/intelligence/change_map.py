from __future__ import annotations

import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from revisionproof.contracts import RevisionSpec
from revisionproof.intelligence.models import ChangeWindow
from revisionproof.media.executor import MediaExecutor
from revisionproof.verification.metrics import apply_punch_in, normalized_similarity, roi_similarity

SAMPLE_FPS = 2
RESIDUAL_THRESHOLD = 0.035
CTA_DELTA_THRESHOLD = 0.06
AUDIO_DELTA_THRESHOLD_DB = 3.0


def _audio_samples(path: Path, duration: float, executor: MediaExecutor) -> np.ndarray:
    descriptor, name = tempfile.mkstemp(prefix="change-map-", suffix=".f32le", dir=path.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        executor.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-t",
                f"{duration:.3f}",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "f32le",
                str(temporary),
            ],
            expected_output=temporary,
        )
        samples = np.fromfile(temporary, dtype=np.float32)
        if not samples.size or not np.isfinite(samples).all():
            raise ValueError("Change Map audio could not be decoded")
        return samples
    finally:
        temporary.unlink(missing_ok=True)


def _rms_db(samples: np.ndarray) -> float:
    if not samples.size:
        raise ValueError("Change Map audio coverage is incomplete")
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    return 20 * math.log10(max(rms, 1e-12))


def measure_frame_pairs(
    source: Path, candidate: Path, spec: RevisionSpec, duration: float, executor: MediaExecutor
) -> list[dict[str, Any]]:
    """Bounded sampled diagnostics. No frame-level embedding or LLM verdict."""
    if not 0 < duration <= 600:
        raise ValueError("Change Map duration is outside the bounded media contract")
    audio_a = _audio_samples(source, duration, executor)
    audio_b = _audio_samples(candidate, duration, executor)
    captures = [cv2.VideoCapture(str(path)) for path in (source, candidate)]
    patch = spec.approved_candidate
    cta = spec.manifest_for("locked_cta")
    full_video = any(element.kind == "VIDEO_CONTENT" for element in spec.locked_elements)
    assert cta.roi is not None
    pairs: list[dict[str, Any]] = []
    try:
        for second in range(math.ceil(duration)):
            end = min(second + 1, duration)
            # Codec padding at the very end is not another meaningful video second.
            if end - second < 0.05:
                break
            audio_start, audio_end = int(second * 16000), int(end * 16000)
            audio_delta = abs(
                _rms_db(audio_a[audio_start:audio_end]) - _rms_db(audio_b[audio_start:audio_end])
            )
            for sample in range(SAMPLE_FPS):
                t = second + (sample + 0.5) * (end - second) / SAMPLE_FPS
                frames = []
                for capture in captures:
                    capture.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                    ok, frame = capture.read()
                    if not ok or frame is None:
                        raise ValueError(f"Change Map frame missing at {t:.3f}s")
                    frames.append(frame)
                original, revised = frames
                if original.shape != revised.shape:
                    raise ValueError("Change Map requires matching source and candidate geometry")
                requested = patch.time_range.start_seconds <= t < patch.time_range.end_seconds
                expected = apply_punch_in(original, patch.scale) if requested else original
                cta_active = cta.time_range.start_seconds <= t < cta.time_range.end_seconds
                pairs.append(
                    {
                        "sample_ms": round(t * 1000),
                        "visual_delta": 1 - normalized_similarity(original, revised),
                        "residual_delta": 1 - normalized_similarity(expected, revised),
                        "cta_delta": 1
                        - roi_similarity(expected if full_video else original, revised, cta.roi)
                        if cta_active
                        else 0.0,
                        "audio_delta_db": audio_delta,
                        "requested": int(requested),
                    }
                )
    finally:
        for capture in captures:
            capture.release()
    return pairs


def classify_window(row: dict[str, Any]) -> ChangeWindow:
    residual = float(row["residual_delta"])
    cta = float(row["cta_delta"])
    audio = float(row["audio_delta_db"])
    requested = bool(int(row["requested"]))
    review = (
        residual > RESIDUAL_THRESHOLD
        or cta > CTA_DELTA_THRESHOLD
        or audio > AUDIO_DELTA_THRESHOLD_DB
    )
    return ChangeWindow(
        second=int(row["second"]),
        sample_count=int(row["sample_count"]),
        visual_delta=float(row["visual_delta"]),
        residual_delta=residual,
        cta_delta=cta,
        audio_delta_db=audio,
        requested=requested,
        status="review" if review else "requested" if requested else "unchanged",
    )


def aggregate_fixture_pairs(pairs: list[dict[str, Any]]) -> list[ChangeWindow]:
    """Explicit fixture equivalent of the incremental MV; never used on the LIVE path."""
    groups: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    for pair in pairs:
        groups[pair["sample_ms"] // 1000][pair["sample_ms"]] = pair
    return [
        classify_window(
            {
                "second": second,
                "sample_count": len(samples),
                **{
                    key: max(row[key] for row in samples.values())
                    for key in (
                        "visual_delta",
                        "residual_delta",
                        "cta_delta",
                        "audio_delta_db",
                        "requested",
                    )
                },
            }
        )
        for second, samples in sorted(groups.items())
    ]
