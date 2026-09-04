from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "runtime" / "demo"
WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 30.0

FONT_REGULAR = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")

BG = (8, 14, 25)
PANEL = (18, 29, 47)
PANEL_SOFT = (25, 40, 62)
WHITE = (242, 247, 255)
MUTED = (153, 171, 196)
CYAN = (82, 220, 238)
BLUE = (73, 120, 255)
MINT = (105, 231, 178)
AMBER = (255, 194, 92)


NARRATION = (
    (0.75, "KANAPP turns real operating problems into practical SaaS products.", 1.0),
    (5.35, "We simplify repeated work across health, documents, and approvals.", 0.42),
    (
        10.25,
        "Medical Check clarifies health data. Lean C O O streamlines business documents.",
        1.0,
    ),
    (18.35, "People review every important decision.", 1.0),
    (
        21.25,
        "We build working products first, then improve them with real operating data.",
        1.0,
    ),
    (27.0, "KANAPP. AI made practical.", 1.0),
)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def _ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _scene_progress(second: float, start: float, end: float) -> float:
    return _ease((second - start) / max(end - start, 0.001))


def _round_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 1,
    radius: int = 22,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int,
    *,
    fill: tuple[int, int, int] = WHITE,
    bold: bool = False,
    anchor: str | None = None,
) -> None:
    draw.text(xy, value, font=_font(size, bold=bold), fill=fill, anchor=anchor)


def _base_frame(second: float, scene_number: int, scene_label: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    glow_x = int(160 + math.sin(second * 0.55) * 40)
    glow_y = int(130 + math.cos(second * 0.45) * 24)
    for radius, alpha in ((300, 12), (220, 15), (140, 18)):
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse(
            (glow_x - radius, glow_y - radius, glow_x + radius, glow_y + radius),
            fill=(*BLUE, alpha),
        )
        image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)

    for x in range(0, WIDTH, 80):
        draw.line((x, 0, x, HEIGHT), fill=(13, 23, 38), width=1)
    for y in range(0, HEIGHT, 80):
        draw.line((0, y, WIDTH, y), fill=(13, 23, 38), width=1)

    _text(draw, (52, 45), "KANAPP", 25, fill=WHITE, bold=True)
    _text(draw, (155, 47), "[ka:nap]", 16, fill=CYAN)
    _text(draw, (1032, 47), f"0{scene_number} / 06", 15, fill=MUTED, bold=True)
    _text(draw, (1188, 47), scene_label.upper(), 15, fill=CYAN, bold=True, anchor="ra")
    draw.line((52, 78, 1228, 78), fill=(39, 58, 82), width=1)

    progress = min(1.0, max(0.0, second / DURATION))
    draw.rounded_rectangle((52, 676, 1228, 680), radius=2, fill=(39, 58, 82))
    draw.rounded_rectangle(
        (52, 676, 52 + int(1176 * progress), 680), radius=2, fill=CYAN
    )
    return image


def _pill(
    draw: ImageDraw.ImageDraw, x: int, y: int, label: str, accent: tuple[int, int, int]
) -> None:
    box = draw.textbbox((0, 0), label, font=_font(17, bold=True))
    width = box[2] - box[0] + 42
    _round_rect(draw, (x, y, x + width, y + 38), fill=PANEL, outline=accent, radius=19)
    _text(draw, (x + 21, y + 19), label, 17, fill=accent, bold=True, anchor="lm")


def _hero(second: float) -> Image.Image:
    image = _base_frame(second, 1, "Introduction")
    draw = ImageDraw.Draw(image)
    intro = _scene_progress(second, 0.0, 1.1)
    x = int(640 + (1.0 - intro) * 55)
    _text(draw, (x, 228), "KANAPP", 92, fill=WHITE, bold=True, anchor="mm")
    _text(draw, (x, 307), "Practical SaaS, powered by AI", 34, fill=CYAN, anchor="mm")
    _round_rect(draw, (350, 374, 930, 501), fill=PANEL, outline=(46, 72, 101), width=2)
    _text(draw, (392, 414), "REAL OPERATING PROBLEMS", 17, fill=MUTED, bold=True)
    _text(
        draw, (392, 454), "Working products people can use", 30, fill=WHITE, bold=True
    )
    _pill(draw, 392, 523, "AI + SOFTWARE + OPERATIONS", MINT)
    return image


def _workflows(second: float) -> Image.Image:
    image = _base_frame(second, 2, "Repeated work")
    draw = ImageDraw.Draw(image)
    _text(draw, (64, 139), "Repeated work, simplified.", 50, fill=WHITE, bold=True)
    _text(
        draw,
        (66, 205),
        "Clear flows for the work teams handle every day.",
        25,
        fill=MUTED,
    )

    cards = (
        (64, "01", "Health records", "Track and interpret", CYAN),
        (458, "02", "Business documents", "Draft and review", BLUE),
        (852, "03", "Approvals", "Keep people in control", MINT),
    )
    pulse = 1.0 + 0.02 * math.sin((second - 5.0) * 2.5)
    for index, (x, number, title, detail, accent) in enumerate(cards):
        y = 279 + int(5 * math.sin(second * 1.5 + index))
        _round_rect(
            draw, (x, y, x + 350, y + 255), fill=PANEL, outline=(42, 64, 91), width=2
        )
        draw.ellipse((x + 28, y + 30, x + 78, y + 80), fill=accent)
        _text(draw, (x + 53, y + 55), number, 16, fill=BG, bold=True, anchor="mm")
        _text(draw, (x + 28, y + 124), title, 27, fill=WHITE, bold=True)
        _text(draw, (x + 28, y + 164), detail, 20, fill=MUTED)
        bar_width = int((240 + index * 20) * pulse)
        draw.rounded_rectangle(
            (x + 28, y + 207, x + 28 + bar_width, y + 216), radius=5, fill=accent
        )
    return image


def _products(second: float) -> Image.Image:
    image = _base_frame(second, 3, "Products")
    draw = ImageDraw.Draw(image)
    _text(draw, (64, 139), "Products built for real use.", 50, fill=WHITE, bold=True)
    _text(draw, (66, 205), "Focused tools, complete operating flows.", 25, fill=MUTED)

    products = (
        (64, "MEDICAL CHECK", "Understand health data", "AI-assisted reports", CYAN),
        (652, "LEANCOO", "Move documents forward", "Draft, review, approve", AMBER),
    )
    for index, (x, name, title, detail, accent) in enumerate(products):
        y = 278
        _round_rect(draw, (x, y, x + 564, y + 284), fill=PANEL, outline=accent, width=2)
        _pill(draw, x + 28, y + 28, name, accent)
        _text(draw, (x + 28, y + 120), title, 31, fill=WHITE, bold=True)
        _text(draw, (x + 28, y + 165), detail, 22, fill=MUTED)
        for row in range(3):
            yy = y + 213 + row * 20
            line = 250 + int(40 * math.sin(second * 1.2 + row + index))
            draw.rounded_rectangle(
                (x + 28, yy, x + 28 + line, yy + 7), radius=4, fill=PANEL_SOFT
            )
        signal_x = x + 476
        signal_y = y + 74
        draw.ellipse(
            (signal_x - 34, signal_y - 34, signal_x + 34, signal_y + 34), fill=accent
        )
        _text(draw, (signal_x, signal_y), "OK", 17, fill=BG, bold=True, anchor="mm")
    return image


def _approval(second: float) -> Image.Image:
    image = _base_frame(second, 4, "Human approval")
    draw = ImageDraw.Draw(image)
    _text(
        draw,
        (640, 144),
        "Human approval stays central.",
        50,
        fill=WHITE,
        bold=True,
        anchor="ma",
    )
    _text(
        draw,
        (640, 207),
        "AI supports the work. People make the decision.",
        25,
        fill=MUTED,
        anchor="ma",
    )

    y = 365
    nodes = (
        (250, "AI DRAFT", BLUE),
        (640, "HUMAN REVIEW", CYAN),
        (1030, "CLEAR DECISION", MINT),
    )
    sweep = _scene_progress(second, 16.0, 19.5)
    draw.line((295, y, 985, y), fill=(45, 69, 98), width=6)
    draw.line((295, y, int(295 + 690 * sweep), y), fill=CYAN, width=6)
    for x, label, accent in nodes:
        draw.ellipse(
            (x - 54, y - 54, x + 54, y + 54), fill=PANEL, outline=accent, width=4
        )
        if x <= int(250 + 780 * sweep):
            draw.ellipse((x - 32, y - 32, x + 32, y + 32), fill=accent)
        _text(draw, (x, y + 100), label, 18, fill=accent, bold=True, anchor="mm")
    _round_rect(draw, (353, 522, 927, 587), fill=PANEL, outline=(43, 66, 94), width=2)
    _text(
        draw,
        (640, 554),
        "A deliberate pause leaves room to review.",
        23,
        fill=MUTED,
        anchor="mm",
    )
    return image


def _process(second: float) -> Image.Image:
    image = _base_frame(second, 5, "Operating loop")
    draw = ImageDraw.Draw(image)
    _text(draw, (64, 139), "Build. Operate. Improve.", 50, fill=WHITE, bold=True)
    _text(
        draw,
        (66, 205),
        "Start with a working product. Learn from real use.",
        25,
        fill=MUTED,
    )

    steps = (
        (120, "01", "FIND", "Repeated problems", CYAN),
        (480, "02", "BUILD", "A complete flow", BLUE),
        (840, "03", "IMPROVE", "Operating data", MINT),
    )
    for index, (x, number, title, detail, accent) in enumerate(steps):
        y = 300 + int(8 * math.sin((second - 20.0) * 1.7 + index))
        _round_rect(draw, (x, y, x + 320, y + 229), fill=PANEL, outline=accent, width=2)
        _text(draw, (x + 26, y + 44), number, 18, fill=accent, bold=True)
        _text(draw, (x + 26, y + 102), title, 31, fill=WHITE, bold=True)
        _text(draw, (x + 26, y + 145), detail, 21, fill=MUTED)
        draw.rounded_rectangle(
            (x + 26, y + 185, x + 294, y + 193), radius=4, fill=PANEL_SOFT
        )
        completed = int(268 * ((second - 20.0) / 6.0 + index * 0.22))
        completed = max(0, min(268, completed))
        draw.rounded_rectangle(
            (x + 26, y + 185, x + 26 + completed, y + 193), radius=4, fill=accent
        )
    return image


def _end_card(second: float) -> Image.Image:
    image = _base_frame(second, 6, "Brand close")
    draw = ImageDraw.Draw(image)
    pulse = 1.0 + 0.015 * math.sin((second - 26.0) * 3.2)
    size = int(94 * pulse)
    _text(draw, (640, 246), "KANAPP", size, fill=WHITE, bold=True, anchor="mm")
    _text(
        draw,
        (640, 337),
        "Practical products, powered by AI.",
        35,
        fill=CYAN,
        anchor="mm",
    )
    _round_rect(draw, (322, 402, 958, 501), fill=PANEL, outline=(46, 72, 101), width=2)
    _text(
        draw,
        (640, 435),
        "BUILT FOR REAL OPERATIONS",
        17,
        fill=MUTED,
        bold=True,
        anchor="ma",
    )
    _text(
        draw,
        (640, 477),
        "Ready for what comes next.",
        27,
        fill=WHITE,
        bold=True,
        anchor="ma",
    )
    # The lower-right area intentionally stays empty for the demo URL overlay.
    return image


def render_frame(second: float) -> np.ndarray:
    if second < 5.0:
        image = _hero(second)
    elif second < 10.0:
        image = _workflows(second)
    elif second < 16.0:
        image = _products(second)
    elif second < 20.5:
        image = _approval(second)
    elif second < 26.0:
        image = _process(second)
    else:
        image = _end_card(second)
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def _run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def generate_voice_parts(parts_dir: Path) -> list[Path]:
    parts_dir.mkdir(parents=True, exist_ok=True)
    script_path = parts_dir / "render_voice.ps1"
    script_lines = [
        "param([string]$OutputDir)",
        "Add-Type -AssemblyName System.Speech",
        "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer",
        "$voice.SelectVoice('Microsoft Zira Desktop')",
        "$voice.Rate = 1",
        "$voice.Volume = 100",
    ]
    destinations: list[Path] = []
    for index, (_, text, _) in enumerate(NARRATION, start=1):
        destination = parts_dir / f"voice-{index:02d}.wav"
        destinations.append(destination)
        safe_text = text.replace("'", "''")
        script_lines.extend(
            (
                f"$voice.SetOutputToWaveFile((Join-Path $OutputDir 'voice-{index:02d}.wav'))",
                f"$voice.Speak('{safe_text}')",
                "$voice.SetOutputToNull()",
            )
        )
    script_lines.append("$voice.Dispose()")
    script_path.write_text("\n".join(script_lines), encoding="utf-8-sig")
    _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-OutputDir",
            str(parts_dir),
        ]
    )
    return destinations


def generate_silent_video(destination: Path) -> None:
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
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
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
        for frame_index in range(round(FPS * DURATION)):
            process.stdin.write(render_frame(frame_index / FPS).tobytes())
    finally:
        process.stdin.close()
    error = process.stderr.read().decode("utf-8", errors="replace")
    if process.wait() != 0:
        raise RuntimeError(f"Video rendering failed: {error.strip()}")


def add_narration(
    silent_video: Path, voice_parts: list[Path], destination: Path
) -> None:
    command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent_video)]
    for part in voice_parts:
        command.extend(("-i", str(part)))

    filters: list[str] = []
    narration_labels: list[str] = []
    for index, ((start, _, volume), _) in enumerate(
        zip(NARRATION, voice_parts), start=1
    ):
        delay_ms = round(start * 1000)
        label = f"voice{index}"
        filters.append(f"[{index}:a]volume={volume},adelay={delay_ms}:all=1[{label}]")
        narration_labels.append(f"[{label}]")

    # A restrained tonal bed drops to complete silence from 15.6s to 18.2s so
    # the quiet-pause finder has a deterministic interval to propose.
    filters.append(
        "sine=frequency=164:sample_rate=48000:duration=30,"
        "volume='if(between(t,15.6,18.2),0,0.018)':eval=frame[bed]"
    )
    filters.append(
        f"[bed]{''.join(narration_labels)}amix=inputs={len(narration_labels) + 1}:"
        "duration=first:normalize=0,alimiter=limit=0.92,atrim=0:30[aout]"
    )
    command.extend(
        (
            "-filter_complex",
            ";".join(filters),
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-t",
            "30",
            "-movflags",
            "+faststart",
            str(destination),
        )
    )
    _run(command)


def generate_logo(destination: Path) -> None:
    image = Image.new("RGBA", (720, 180), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (8, 8, 704, 164),
        radius=34,
        fill=(8, 14, 25, 232),
        outline=(*CYAN, 255),
        width=4,
    )
    draw.ellipse((38, 43, 118, 123), fill=(*CYAN, 255))
    _text(draw, (78, 83), "K", 38, fill=BG, bold=True, anchor="mm")
    _text(draw, (148, 78), "KANAPP", 54, fill=WHITE, bold=True, anchor="lm")
    _text(
        draw, (151, 126), "PRACTICAL AI PRODUCTS", 18, fill=CYAN, bold=True, anchor="lm"
    )
    image.save(destination)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the 30-second editable KANAPP English promo source."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "kanapp_english_editable_source_30s.mp4",
    )
    args = parser.parse_args()

    destination = args.output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    work_dir = destination.parent / "kanapp-promo-parts"
    silent_video = work_dir / "silent-video.mp4"
    voice_parts = generate_voice_parts(work_dir)
    generate_silent_video(silent_video)
    add_narration(silent_video, voice_parts, destination)
    logo = destination.parent / "kanapp_demo_logo.png"
    generate_logo(logo)
    print(f"generated {destination}")
    print(f"generated {logo}")


if __name__ == "__main__":
    main()
