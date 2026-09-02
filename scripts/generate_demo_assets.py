from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "runtime" / "demo"

WIDTH = 1280
HEIGHT = 720
FPS = 24
DURATION_SECONDS = 30
BASE_VOLUME = 0.08

INK = (24, 20, 14)
NAVY = (35, 25, 12)
PANEL = (54, 39, 23)
PANEL_LIGHT = (76, 56, 34)
MUTED = (164, 150, 130)
WHITE = (248, 248, 246)
CYAN = (255, 226, 90)
PURPLE = (255, 104, 137)
GREEN = (163, 236, 105)
AMBER = (79, 183, 255)
RED = (103, 103, 255)


def _text(
    frame: np.ndarray,
    value: str,
    x: int,
    y: int,
    *,
    scale: float = 0.6,
    color: tuple[int, int, int] = WHITE,
    thickness: int = 1,
) -> None:
    cv2.putText(
        frame,
        value,
        (x, y),
        cv2.FONT_HERSHEY_DUPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def _rounded_box(
    frame: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int,
    color: tuple[int, int, int],
    *,
    radius: int = 16,
    border: tuple[int, int, int] | None = None,
    alpha: float = 1.0,
) -> None:
    overlay = frame.copy()
    x2 = x + width
    y2 = y + height
    cv2.rectangle(overlay, (x + radius, y), (x2 - radius, y2), color, -1)
    cv2.rectangle(overlay, (x, y + radius), (x2, y2 - radius), color, -1)
    for center in (
        (x + radius, y + radius),
        (x2 - radius, y + radius),
        (x + radius, y2 - radius),
        (x2 - radius, y2 - radius),
    ):
        cv2.circle(overlay, center, radius, color, -1)
    if alpha < 1.0:
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
    else:
        frame[:] = overlay
    if border is not None:
        cv2.rectangle(frame, (x + radius, y), (x2 - radius, y2), border, 1)
        cv2.rectangle(frame, (x, y + radius), (x2, y2 - radius), border, 1)
        for center in (
            (x + radius, y + radius),
            (x2 - radius, y + radius),
            (x + radius, y2 - radius),
            (x2 - radius, y2 - radius),
        ):
            cv2.circle(frame, center, radius, border, 1)


def _background(second: float) -> np.ndarray:
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    frame[:] = NAVY
    glow_x = int(180 + 25 * math.sin(second * 0.8))
    glow_y = int(155 + 18 * math.cos(second * 0.6))
    overlay = frame.copy()
    cv2.circle(overlay, (glow_x, glow_y), 290, PURPLE, -1)
    cv2.circle(overlay, (1090, 650), 360, CYAN, -1)
    cv2.addWeighted(overlay, 0.07, frame, 0.93, 0, frame)
    for x in range(0, WIDTH, 64):
        cv2.line(frame, (x, 0), (x, HEIGHT), (42, 33, 22), 1)
    for y in range(0, HEIGHT, 64):
        cv2.line(frame, (0, y), (WIDTH, y), (42, 33, 22), 1)
    return frame


def _header(frame: np.ndarray, scene: str, title: str) -> None:
    _rounded_box(frame, 44, 30, 1192, 54, INK, border=PANEL_LIGHT, alpha=0.94)
    _text(frame, "REVISIONPROOF", 68, 65, scale=0.72, color=CYAN, thickness=2)
    _text(frame, scene, 910, 63, scale=0.45, color=MUTED)
    _text(frame, title, 1004, 64, scale=0.55, color=WHITE, thickness=2)


def _timeline(frame: np.ndarray, second: float) -> None:
    y = 682
    cv2.line(frame, (70, y), (1210, y), PANEL_LIGHT, 5)
    progress = max(0.0, min(1.0, second / DURATION_SECONDS))
    cv2.line(frame, (70, y), (70 + int(1140 * progress), y), CYAN, 5)
    marker_x = 70 + int(1140 * progress)
    cv2.circle(frame, (marker_x, y), 8, WHITE, -1)
    _text(frame, f"{second:04.1f}s", 70, 663, scale=0.42, color=MUTED)
    _text(frame, "VISUAL QA SAMPLE", 1030, 663, scale=0.42, color=MUTED)


def _person(frame: np.ndarray, x: int, y: int, *, pointing: bool) -> None:
    cv2.circle(frame, (x, y), 44, (189, 191, 232), -1)
    cv2.ellipse(frame, (x, y - 15), (46, 33), 0, 180, 360, (55, 43, 34), -1)
    cv2.circle(frame, (x - 15, y + 2), 4, INK, -1)
    cv2.circle(frame, (x + 15, y + 2), 4, INK, -1)
    cv2.ellipse(frame, (x, y + 18), (14, 7), 0, 0, 180, (83, 66, 54), 2)
    cv2.ellipse(frame, (x, y + 130), (82, 118), 0, 180, 360, PURPLE, -1)
    cv2.line(frame, (x - 68, y + 96), (x - 112, y + 160), PURPLE, 24)
    if pointing:
        cv2.line(frame, (x + 62, y + 98), (x + 150, y + 40), PURPLE, 24)
        cv2.circle(frame, (x + 160, y + 34), 12, (189, 191, 232), -1)
    else:
        cv2.line(frame, (x + 62, y + 98), (x + 106, y + 160), PURPLE, 24)


def _editing_scene(frame: np.ndarray, second: float) -> None:
    _header(frame, "SCENE 01", "CLIENT NOTE")
    _rounded_box(frame, 54, 108, 1172, 526, PANEL, border=PANEL_LIGHT, alpha=0.98)
    _person(frame, 160, 255, pointing=False)
    _rounded_box(frame, 275, 132, 916, 104, INK, border=PURPLE)
    _text(frame, "CLIENT FEEDBACK", 302, 162, scale=0.43, color=MUTED)
    _text(
        frame,
        '"When the presenter says RevisionProof, push in slightly."',
        302,
        205,
        scale=0.68,
        thickness=2,
    )
    _rounded_box(frame, 275, 258, 610, 334, INK, border=PANEL_LIGHT)
    _text(frame, "EDIT TIMELINE", 302, 290, scale=0.42, color=MUTED)
    for row, (label, color) in enumerate(
        (("VIDEO 01", PURPLE), ("B-ROLL", CYAN), ("AUDIO", GREEN))
    ):
        y = 335 + row * 72
        _text(frame, label, 302, y + 20, scale=0.42, color=MUTED)
        cv2.rectangle(frame, (405, y), (840, y + 38), (35, 29, 22), -1)
        clip_start = 430 + row * 38
        moving_width = int(190 + 18 * math.sin(second * 1.7 + row))
        cv2.rectangle(
            frame, (clip_start, y + 5), (clip_start + moving_width, y + 33), color, -1
        )
        cv2.line(frame, (655, y - 8), (655, y + 46), WHITE, 2)
    _rounded_box(frame, 910, 258, 250, 334, (30, 27, 23), border=PANEL_LIGHT)
    _text(frame, "AGENT READ", 934, 294, scale=0.42, color=CYAN)
    items = (
        ("1", "Find the phrase", GREEN),
        ("2", "Anchor the scene", GREEN),
        ("3", "Render A / B", AMBER),
        ("4", "Verify constraints", MUTED),
    )
    for index, (number, label, color) in enumerate(items):
        y = 342 + index * 56
        cv2.circle(frame, (938, y), 14, color, -1)
        _text(frame, number, 933, y + 5, scale=0.38, color=INK, thickness=2)
        _text(frame, label, 966, y + 6, scale=0.43, color=WHITE)
    _text(
        frame, "Ambiguity becomes an executable edit.", 302, 620, scale=0.48, color=CYAN
    )


def _reveal_scene(frame: np.ndarray, second: float) -> None:
    _header(frame, "SCENE 02", "PRODUCT REVEAL")
    pulse = 1.0 + 0.015 * math.sin((second - 8.0) * 4.0)
    card_w = int(690 * pulse)
    card_h = int(410 * pulse)
    card_x = 520 - card_w // 2 + 245
    card_y = 118 + (410 - card_h) // 2
    _rounded_box(frame, card_x, card_y, card_w, card_h, PANEL, border=PURPLE)
    _person(frame, 177, 275, pointing=True)
    _rounded_box(
        frame, card_x + 38, card_y + 34, card_w - 76, 42, INK, border=PANEL_LIGHT
    )
    _text(
        frame,
        "LIVE PROOF TRACE",
        card_x + 58,
        card_y + 61,
        scale=0.44,
        color=GREEN,
        thickness=2,
    )
    _text(
        frame,
        "RevisionProof",
        card_x + 92,
        card_y + 172,
        scale=1.38,
        color=WHITE,
        thickness=3,
    )
    _text(frame, "FEEDBACK", card_x + 62, card_y + 252, scale=0.43, color=MUTED)
    _text(frame, "EVIDENCE", card_x + 275, card_y + 252, scale=0.43, color=MUTED)
    _text(frame, "APPROVED", card_x + 478, card_y + 252, scale=0.43, color=MUTED)
    cv2.circle(frame, (card_x + 130, card_y + 298), 22, PURPLE, -1)
    cv2.circle(frame, (card_x + 340, card_y + 298), 22, CYAN, -1)
    cv2.circle(frame, (card_x + 535, card_y + 298), 22, GREEN, -1)
    cv2.line(
        frame,
        (card_x + 152, card_y + 298),
        (card_x + 318, card_y + 298),
        PANEL_LIGHT,
        5,
    )
    cv2.line(
        frame,
        (card_x + 362, card_y + 298),
        (card_x + 513, card_y + 298),
        PANEL_LIGHT,
        5,
    )
    _text(frame, "NOTE", card_x + 111, card_y + 305, scale=0.28, color=INK, thickness=2)
    _text(
        frame, "08-14", card_x + 315, card_y + 305, scale=0.28, color=INK, thickness=2
    )
    _text(frame, "PASS", card_x + 514, card_y + 305, scale=0.28, color=INK, thickness=2)
    _rounded_box(frame, 76, 515, 1128, 95, INK, border=CYAN)
    _text(frame, "CAMERA PUSH-IN TARGET", 106, 553, scale=0.45, color=CYAN, thickness=2)
    _text(
        frame,
        "The wordmark and proof trace stay centered from 00:08 to 00:14.",
        106,
        584,
        scale=0.56,
        color=WHITE,
    )


def _proof_scene(frame: np.ndarray, second: float) -> None:
    _header(frame, "SCENE 03", "CONSTRAINED OPTIONS")
    _text(
        frame,
        "Same intent. Measurable choices.",
        64,
        128,
        scale=0.75,
        color=WHITE,
        thickness=2,
    )
    cards = (
        (64, "SOURCE", "1.00x", MUTED),
        (438, "OPTION A", "1.05x", CYAN),
        (812, "OPTION B", "1.12x", PURPLE),
    )
    for index, (x, label, scale_label, accent) in enumerate(cards):
        _rounded_box(frame, x, 166, 340, 418, PANEL, border=accent)
        _text(frame, label, x + 26, 205, scale=0.48, color=accent, thickness=2)
        _text(frame, scale_label, x + 245, 205, scale=0.48, color=WHITE, thickness=2)
        inset = 23 - index * 6
        cv2.rectangle(
            frame,
            (x + 30 + inset, 242 + inset),
            (x + 310 - inset, 402 - inset),
            INK,
            -1,
        )
        cv2.rectangle(
            frame,
            (x + 102 - index * 10, 280 - index * 7),
            (x + 238 + index * 10, 360 + index * 7),
            accent,
            -1,
        )
        cv2.rectangle(
            frame,
            (x + 122 - index * 8, 300 - index * 5),
            (x + 218 + index * 8, 340 + index * 5),
            PANEL,
            -1,
        )
        if index == 0:
            status, status_color = "REFERENCE", MUTED
        elif index == 1:
            status, status_color = "SAFE", GREEN
        else:
            status, status_color = "STRONG", GREEN
        _rounded_box(frame, x + 28, 444, 284, 50, INK, border=status_color)
        _text(frame, status, x + 48, 476, scale=0.48, color=status_color, thickness=2)
        _text(frame, "Audio +/-2 dB   CTA locked", x + 28, 537, scale=0.40, color=MUTED)
    sweep_x = 64 + int(((second - 14.0) % 3.0) / 3.0 * 1088)
    cv2.line(frame, (sweep_x, 596), (sweep_x + 70, 596), CYAN, 4)
    _text(
        frame,
        "A/B PREVIEWS ARE EDITS YOU CAN SEE, NOT JUST JSON.",
        64,
        628,
        scale=0.48,
        color=CYAN,
        thickness=2,
    )


def _end_card(frame: np.ndarray, second: float) -> None:
    _header(frame, "SCENE 04", "VERIFIED DELIVERY")
    _rounded_box(frame, 62, 114, 1110, 426, PANEL, border=GREEN)
    _text(frame, "RevisionProof", 115, 215, scale=1.48, color=WHITE, thickness=3)
    _text(
        frame,
        "Every revision ends with evidence.",
        118,
        260,
        scale=0.68,
        color=CYAN,
        thickness=2,
    )
    checks = (
        ("GEMINI INTERPRETATION", "LIVE"),
        ("CLICKHOUSE EVIDENCE", "3 MATCHES"),
        ("OPENCV + FFMPEG VERDICT", "PASS"),
    )
    for index, (label, value) in enumerate(checks):
        y = 318 + index * 62
        cv2.circle(frame, (132, y), 16, GREEN, -1)
        _text(frame, "OK", 122, y + 5, scale=0.32, color=INK, thickness=2)
        _text(frame, label, 170, y + 7, scale=0.48, color=MUTED)
        _text(frame, value, 900, y + 7, scale=0.48, color=GREEN, thickness=2)
    cta_color = CYAN if int((second - 24.0) * 2) % 2 == 0 else (235, 211, 86)
    cv2.rectangle(frame, (840, 570), (1180, 660), cta_color, -1)
    cv2.rectangle(frame, (856, 586), (1164, 644), INK, -1)
    _text(frame, "APPROVE DELIVERY", 884, 623, scale=0.66, color=WHITE, thickness=2)
    _text(frame, "CTA SAFE ZONE", 953, 559, scale=0.38, color=CYAN)
    cv2.rectangle(frame, (72, 570), (760, 660), INK, -1)
    _text(frame, "END-CARD CONSTRAINT", 94, 604, scale=0.42, color=MUTED)
    _text(
        frame,
        "The approval CTA must remain pixel-safe.",
        94,
        638,
        scale=0.57,
        color=WHITE,
        thickness=2,
    )


def render_frame(second: float) -> np.ndarray:
    frame = _background(second)
    if second < 8.0:
        _editing_scene(frame, second)
    elif second < 14.0:
        _reveal_scene(frame, second)
    elif second < 24.0:
        _proof_scene(frame, second)
    else:
        _end_card(frame, second)
    _timeline(frame, second)
    return frame


def generate_source(destination: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=220:sample_rate=48000:duration={DURATION_SECONDS}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-af",
        f"volume={BASE_VOLUME}",
        "-shortest",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stderr is not None
    try:
        for frame_index in range(FPS * DURATION_SECONDS):
            process.stdin.write(render_frame(frame_index / FPS).tobytes())
    finally:
        process.stdin.close()
    error = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg source generation failed: {error.strip()}")
    print(f"generated {destination.relative_to(ROOT)}")


def variant_filter(*, punch_scale: float | None, cta_mode: str) -> str | None:
    filters: list[str] = []
    if punch_scale is not None:
        crop_width = round(WIDTH / punch_scale)
        crop_height = round(HEIGHT / punch_scale)
        filters.append(
            "split=2[normal][zoom];"
            f"[zoom]crop={crop_width}:{crop_height}:"
            f"(iw-{crop_width})/2:(ih-{crop_height})/2,scale={WIDTH}:{HEIGHT}[zoomed];"
            "[normal][zoomed]overlay=enable='between(t,8,14)'"
        )
    if cta_mode in {"remove", "partial", "shifted"}:
        start = 25 if cta_mode == "partial" else 24
        filters.append(
            f"drawbox=enable='between(t,{start},29)':x=840:y=570:"
            "w=340:h=90:color=0x0e1423@1:t=fill"
        )
    if cta_mode == "shifted":
        filters.extend(
            (
                (
                    "drawbox=enable='between(t,24,29)':x=420:y=570:"
                    "w=340:h=90:color=0x5ae2ff@1:t=fill"
                ),
                (
                    "drawbox=enable='between(t,24,29)':x=438:y=588:"
                    "w=304:h=54:color=0x0e1423@1:t=fill"
                ),
            )
        )
    return ",".join(filters) if filters else None


def generate_variant(
    source: Path,
    filename: str,
    *,
    punch_scale: float | None,
    cta_mode: str,
    volume: float = BASE_VOLUME,
) -> None:
    destination = DEMO_DIR / filename
    command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(source)]
    filter_graph = variant_filter(punch_scale=punch_scale, cta_mode=cta_mode)
    if filter_graph is not None:
        command.extend(("-vf", filter_graph))
    command.extend(
        (
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-af",
            f"volume={volume / BASE_VOLUME}",
            "-movflags",
            "+faststart",
            str(destination),
        )
    )
    subprocess.run(command, check=True, capture_output=True, text=True)
    print(f"generated {destination.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic, visually inspectable RevisionProof videos."
    )
    parser.add_argument(
        "--demo-only",
        action="store_true",
        help="Generate only the runtime demo assets, excluding the test corpus.",
    )
    args = parser.parse_args()

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    source = DEMO_DIR / "revisionproof_v1.mp4"
    generate_source(source)
    demo_cases = [
        ("revisionproof_v2_blocked_A.mp4", 1.05, "remove", BASE_VOLUME),
        ("revisionproof_v3_ready_A.mp4", 1.05, "preserve", BASE_VOLUME),
        ("revisionproof_v2_blocked.mp4", 1.12, "remove", BASE_VOLUME),
        ("revisionproof_v3_ready.mp4", 1.12, "preserve", BASE_VOLUME),
    ]
    regression_cases = [
        ("regression_pass_audio_plus2db.mp4", 1.12, "preserve", 0.10),
        ("regression_pass_audio_minus2db.mp4", 1.12, "preserve", 0.064),
        ("regression_fail_wrong_scale.mp4", 1.05, "preserve", BASE_VOLUME),
        ("regression_fail_no_patch.mp4", None, "preserve", BASE_VOLUME),
        ("regression_fail_loud_audio.mp4", 1.12, "preserve", 0.16),
        ("regression_fail_clipped_audio.mp4", 1.12, "preserve", 8.0),
        ("regression_fail_silent_audio.mp4", 1.12, "preserve", 0.0),
        ("regression_fail_partial_cta.mp4", 1.12, "partial", BASE_VOLUME),
        ("regression_fail_shifted_cta.mp4", 1.12, "shifted", BASE_VOLUME),
        ("regression_fail_patch_and_cta.mp4", 1.05, "remove", BASE_VOLUME),
    ]
    cases = demo_cases if args.demo_only else [*demo_cases, *regression_cases]
    for filename, punch_scale, cta_mode, volume in cases:
        generate_variant(
            source,
            filename,
            punch_scale=punch_scale,
            cta_mode=cta_mode,
            volume=volume,
        )


if __name__ == "__main__":
    main()
