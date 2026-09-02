from pathlib import Path

import cv2
import numpy as np


def _frame(video: Path, second: float) -> np.ndarray:
    capture = cv2.VideoCapture(str(video))
    capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
    ok, frame = capture.read()
    capture.release()
    assert ok, f"could not read {video.name} at {second}s"
    return frame


def test_demo_source_has_four_visually_distinct_storyboard_scenes(
    runtime_dir: Path,
) -> None:
    # Regression: ISSUE-001 — the old demo looked like an empty geometric video.
    # Found by /qa on 2026-09-02
    # Report: .gstack/qa-reports/qa-report-demo-assets-2026-09-02.md
    source = runtime_dir / "demo" / "revisionproof_v1.mp4"
    frames = [_frame(source, second) for second in (4, 11, 18, 26)]

    assert all(float(frame.std()) > 30 for frame in frames)
    assert all(float(np.mean(cv2.Canny(frame, 80, 160) > 0)) > 0.025 for frame in frames)
    assert all(
        float(np.mean(cv2.absdiff(before, after))) > 12
        for before, after in zip(frames[:-1], frames[1:], strict=True)
    )


def test_demo_candidates_make_punch_and_cta_outcomes_visible(runtime_dir: Path) -> None:
    demo_dir = runtime_dir / "demo"
    source_reveal = _frame(demo_dir / "revisionproof_v1.mp4", 11)
    option_a_reveal = _frame(demo_dir / "revisionproof_v3_ready_A.mp4", 11)
    option_b_reveal = _frame(demo_dir / "revisionproof_v3_ready.mp4", 11)

    assert float(np.mean(cv2.absdiff(source_reveal, option_a_reveal))) > 8
    assert float(np.mean(cv2.absdiff(option_a_reveal, option_b_reveal))) > 8

    source_cta = _frame(demo_dir / "revisionproof_v1.mp4", 26)[570:660, 840:1180]
    blocked_cta = _frame(demo_dir / "revisionproof_v2_blocked.mp4", 26)[570:660, 840:1180]
    ready_cta = _frame(demo_dir / "revisionproof_v3_ready.mp4", 26)[570:660, 840:1180]

    assert float(np.mean(cv2.absdiff(source_cta, blocked_cta))) > 40
    assert float(np.mean(cv2.absdiff(source_cta, ready_cta))) < 3
