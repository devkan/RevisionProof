"""Render approved timeline, audio, text, and frozen logo edits with ffmpeg."""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from revisionproof.editing.models import EditOperation, EditPlan
from revisionproof.editing.sampling import FPS
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.preview import punch_in_filter


def font_path() -> Path:
    for name in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ):
        path = Path(name)
        if path.is_file():
            return path
    raise ValueError("The Korean/English caption font is missing. Install Noto Sans CJK.")


def text_layer(op: EditOperation, destination: Path, appearance: str) -> None:
    font = ImageFont.truetype(str(font_path()), 34 if appearance == "A" else 44)
    image = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    lines = []
    for paragraph in op.text.split("\n"):
        line = ""
        for char in paragraph:
            if line and draw.textlength(line + char, font=font) > 1080:
                lines.append(line)
                line = ""
            line += char
        lines.append(line)
    if len(lines) > 5:
        raise ValueError("This caption is too tall. Split it into shorter timed captions.")
    content = "\n".join(lines)
    box = draw.multiline_textbbox((0, 0), content, font=font, spacing=8, stroke_width=1)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (
        64
        if op.position in {"top_left", "bottom_left"}
        else 1216 - width
        if op.position in {"top_right", "bottom_right"}
        else (1280 - width) / 2
    )
    y = (
        64
        if op.position in {"top", "top_left", "top_right"}
        else ((720 - height) / 2 if op.position == "center" else 648 - height)
    )
    draw.rounded_rectangle(
        (x - 18, y - 14, x + width + 18, y + height + 14),
        radius=10,
        fill=(8, 12, 22, 210 if appearance == "A" else 235),
    )
    draw.multiline_text(
        (x - box[0], y - box[1]),
        content,
        font=font,
        fill="white",
        spacing=8,
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255),
        align="center",
    )
    image.save(destination)


def decode_channels(source: Path, destination: Path, executor: MediaExecutor) -> np.ndarray:
    metadata = json.loads(
        executor.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=channels",
                "-of",
                "json",
                str(source),
            ]
        )
    )
    channels = int(metadata["streams"][0]["channels"])
    if not 1 <= channels <= 8:
        raise ValueError("Silence detection supports audio with 1 to 8 channels.")
    executor.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-vn",
            "-map",
            "0:a:0",
            "-ar",
            "16000",
            "-f",
            "f32le",
            str(destination),
        ],
        expected_output=destination,
    )
    samples = np.fromfile(destination, dtype=np.float32)
    if not samples.size or samples.size % channels or not np.isfinite(samples).all():
        raise ValueError("Audio could not be analysed. Keep the original audio and try again.")
    return samples.reshape(-1, channels)


def resolve_plan(
    plan: EditPlan, duration: float, source: Path, executor: MediaExecutor
) -> tuple[EditPlan, list[str]]:
    if abs(plan.source_duration - duration) > 0.15:
        raise ValueError("This plan belongs to a different video. Review its times again.")
    duration = math.floor((duration + 0.001) * FPS) / FPS
    warnings = []
    operations = []
    audio = None
    remaining = 24 - sum(op.kind != "remove_silence" for op in plan.operations)
    for op in plan.operations:
        start = round(op.start * FPS) / FPS
        end = min(duration, round(op.end * FPS) / FPS)
        if end <= start:
            raise ValueError("An edit is shorter than one video frame.")
        if op.kind != "remove_silence":
            operations.append(
                EditOperation.model_validate({**op.model_dump(), "start": start, "end": end})
            )
            continue
        if audio is None:
            with tempfile.TemporaryDirectory(prefix="silence-", dir=source.parent) as folder:
                audio = decode_channels(source, Path(folder) / "audio.f32", executor)
        # Every channel must be quiet. Never downmix: opposite-phase stereo can cancel.
        block = 320  # 20 ms at 16 kHz
        quiet = []
        for offset in range(int(start * 16000), min(len(audio), int(end * 16000)), block):
            frame = audio[offset : min(offset + block, int(end * 16000))]
            rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2, axis=0)).max()
            quiet.append(20 * math.log10(max(float(rms), 1e-12)) < op.threshold_db)
        spans = []
        beginning = None
        for index, is_quiet in enumerate([*quiet, False]):
            if is_quiet and beginning is None:
                beginning = index
            elif not is_quiet and beginning is not None:
                a, b = start + beginning * 0.02, min(end, start + index * 0.02)
                if b - a >= op.min_silence:
                    a, b = math.ceil((a + 0.12) * FPS) / FPS, math.floor((b - 0.12) * FPS) / FPS
                    if b - a >= 0.1:
                        spans.append(EditOperation(kind="cut", start=a, end=b, detected=True))
                beginning = None
        if not spans:
            warnings.append("No quiet pause met these settings. No silence was removed.")
        elif sum(s.end - s.start for s in spans) >= duration - 1:
            warnings.append(
                "Almost the whole video is quiet. "
                "Automatic removal was held back; choose a cut manually."
            )
        else:
            if len(spans) > remaining:
                omitted = len(spans) - remaining
                spans = sorted(
                    sorted(spans, key=lambda s: s.end - s.start, reverse=True)[:remaining],
                    key=lambda s: s.start,
                )
                warnings.append(
                    f"{omitted} additional pause(s) exceed the 24-edit limit. "
                    "Only the longest pauses are proposed; other audio is kept."
                )
            operations.extend(spans)
            remaining -= len(spans)
            warnings.append(
                f"{len(spans)} quiet pause(s) proposed. Select the cuts you want before previewing."
            )
    return EditPlan(source_duration=duration, operations=tuple(operations)), warnings


def render_plan(
    source: Path,
    destination: Path,
    plan: EditPlan,
    appearance: str,
    executor: MediaExecutor,
    logo_root: Path | None = None,
) -> Path:
    if not plan.operations or any(op.kind == "remove_silence" for op in plan.operations):
        raise ValueError("Review and resolve the edit plan before rendering.")
    plan.validate_selection()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="edit-layers-", dir=destination.parent) as folder:
        args = ["ffmpeg", "-y", "-v", "error", "-i", str(source)]
        graph, current, layer_index = [], "0:v", 0
        # Captions remain above logos and attached to source time when a scene is sped up.
        visual_priority = {"zoom": 0, "logo": 1, "text": 2, "subtitle": 2}
        ordered = sorted(
            (op for op in plan.operations if op.kind in visual_priority),
            key=lambda op: visual_priority[op.kind],
        )
        for index, op in enumerate(ordered):
            enabled = f"gte(t,{op.start:.9f})*lt(t,{op.end:.9f})"
            output = f"v{index}"
            if op.kind == "zoom":
                graph += [
                    f"[{current}]split=2[base{index}][in{index}]",
                    f"[in{index}]{punch_in_filter(1.05 if appearance == 'A' else 1.12)}"
                    f"[zoom{index}]",
                    f"[base{index}][zoom{index}]overlay=0:0:enable='{enabled}'[{output}]",
                ]
            elif op.kind in {"text", "subtitle"}:
                layer_index += 1
                layer = Path(folder) / f"layer{index}.png"
                text_layer(op, layer, appearance)
                args += ["-loop", "1", "-framerate", "30", "-i", str(layer)]
                graph.append(
                    f"[{current}][{layer_index}:v]overlay=0:0:enable='{enabled}':shortest=1[{output}]"
                )
            else:
                if logo_root is None:
                    raise ValueError("The uploaded logo is unavailable. Upload it again.")
                logo = (logo_root / f"{op.asset_id}.png").resolve()
                root = logo_root.resolve()
                if logo.parent != root or not logo.is_file():
                    raise ValueError("The uploaded logo is unavailable. Upload it again.")
                with logo.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest != op.asset_sha256:
                    raise ValueError("The uploaded logo changed. Upload it again.")
                layer_index += 1
                args += ["-loop", "1", "-framerate", "30", "-i", str(logo)]
                width = 190 if appearance == "A" else 250
                x = (
                    "48"
                    if op.position in {"top_left", "bottom_left"}
                    else "W-w-48"
                    if op.position in {"top_right", "bottom_right"}
                    else "(W-w)/2"
                )
                y = (
                    "48"
                    if op.position in {"top", "top_left", "top_right"}
                    else "(H-h)/2"
                    if op.position == "center"
                    else "H-h-48"
                )
                graph += [
                    f"[{layer_index}:v]scale={width}:-1,format=rgba,colorchannelmixer=aa=0.92[logo{index}]",
                    f"[{current}][logo{index}]overlay=x={x}:y={y}:enable='{enabled}':shortest=1[{output}]",
                ]
            current = output
        audio = "0:a"
        volume_edits = [op for op in plan.operations if op.kind == "volume"]
        for index, op in enumerate(volume_edits):
            output = f"avol{index}"
            value = "0" if op.volume_db <= -60 else f"{op.volume_db:.3f}dB"
            graph.append(
                f"[{audio}]volume={value}:enable='gte(t,{op.start:.9f})*lt(t,{op.end:.9f})'[{output}]"
            )
            audio = output
        # Trim and retime video/audio by the same original-time boundaries.
        spans = plan.kept_spans
        retimed = any(op.kind in {"cut", "speed"} for op in plan.operations)
        if retimed:
            if len(spans) > 1:
                graph.append(
                    f"[{current}]split={len(spans)}"
                    + "".join(f"[sv{i}]" for i in range(len(spans)))
                )
                graph.append(
                    f"[{audio}]asplit={len(spans)}" + "".join(f"[sa{i}]" for i in range(len(spans)))
                )
            else:
                graph += [f"[{current}]null[sv0]", f"[{audio}]anull[sa0]"]
            for i, span in enumerate(spans):
                graph += [
                    f"[sv{i}]trim=start={span.source_start:.9f}:end={span.source_end:.9f},"
                    f"setpts=(PTS-STARTPTS)/{span.rate:.9f}[vcut{i}]",
                    f"[sa{i}]atrim=start={span.source_start:.9f}:end={span.source_end:.9f},"
                    f"asetpts=PTS-STARTPTS,atempo={span.rate:.9f}[acut{i}]",
                ]
            if len(spans) > 1:
                graph.append(
                    "".join(f"[vcut{i}][acut{i}]" for i in range(len(spans)))
                    + f"concat=n={len(spans)}:v=1:a=1[outv][outa]"
                )
            else:
                graph += ["[vcut0]null[outv]", "[acut0]anull[outa]"]
        else:
            graph.append(f"[{current}]null[outv]")
            if volume_edits:
                graph.append(f"[{audio}]anull[outa]")
        executor.run(
            [
                *args,
                "-filter_complex_threads",
                "1",
                "-filter_complex",
                ";".join(graph),
                "-map",
                "[outv]",
                "-map",
                "[outa]" if retimed or volume_edits else "0:a",
                "-t",
                f"{plan.output_duration:.9f}",
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
                "aac" if retimed or volume_edits else "copy",
                "-movflags",
                "+faststart",
                str(destination),
            ],
            expected_output=destination,
        )
    return destination
