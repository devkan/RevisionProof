from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "runtime" / "demo"


def video_filter(*, punch_scale: float | None, cta_mode: str) -> str:
    base_filters = [
        "drawbox=x=80:y=90:w=1120:h=500:color=0x121a36@0.75:t=fill",
        "drawbox=x=120:y=140:w=1040:h=400:color=0x29345e@0.85:t=fill",
        "drawbox=x='140+mod(t*90,840)':y=310:w=160:h=12:color=0x6ae4ff@0.95:t=fill",
        "drawbox=x=470:y=250:w=340:h=180:color=0x805dff@0.85:t=fill",
        "drawbox=x=495:y=275:w=290:h=130:color=0x11182f@1:t=fill",
    ]
    graph = ",".join(base_filters)
    if punch_scale is not None:
        crop_width = round(1280 / punch_scale)
        crop_height = round(720 / punch_scale)
        graph += (
            ",split=2[normal][zoom];"
            f"[zoom]crop={crop_width}:{crop_height}:"
            f"(iw-{crop_width})/2:(ih-{crop_height})/2,scale=1280:720[zoomed];"
            "[normal][zoomed]overlay=enable='between(t,8,14)'"
        )
    if cta_mode != "none":
        time_window = (
            "between(t,24,25)" if cta_mode == "partial" else "between(t,24,29)"
        )
        x_position = 420 if cta_mode == "shifted" else 840
        graph += (
            f",drawbox=enable='{time_window}':x={x_position}:y=570:"
            "w=340:h=90:color=0x6ae4ff@1:t=fill,"
            f"drawbox=enable='{time_window}':x={x_position + 18}:y=588:"
            "w=304:h=54:color=0x10152b@1:t=fill"
        )
    return graph


def generate(
    filename: str,
    *,
    punch_scale: float | None,
    cta_mode: str,
    volume: float = 0.08,
) -> None:
    destination = DEMO_DIR / filename
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x080c1c:s=1280x720:r=24:d=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:sample_rate=48000:duration=30",
        "-vf",
        video_filter(punch_scale=punch_scale, cta_mode=cta_mode),
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
        f"volume={volume}",
        "-shortest",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    print(f"generated {destination.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic RevisionProof videos."
    )
    parser.add_argument(
        "--demo-only",
        action="store_true",
        help="Generate only the three runtime demo assets, excluding the test corpus.",
    )
    args = parser.parse_args()

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    generate("revisionproof_v1.mp4", punch_scale=None, cta_mode="full")
    demo_cases = [
        ("revisionproof_v2_blocked_A.mp4", 1.05, "none", 0.08),
        ("revisionproof_v3_ready_A.mp4", 1.05, "full", 0.08),
        ("revisionproof_v2_blocked.mp4", 1.12, "none", 0.08),
        ("revisionproof_v3_ready.mp4", 1.12, "full", 0.08),
    ]
    regression_cases = [
        ("regression_pass_audio_plus2db.mp4", 1.12, "full", 0.10),
        ("regression_pass_audio_minus2db.mp4", 1.12, "full", 0.064),
        ("regression_fail_wrong_scale.mp4", 1.05, "full", 0.08),
        ("regression_fail_no_patch.mp4", None, "full", 0.08),
        ("regression_fail_loud_audio.mp4", 1.12, "full", 0.16),
        ("regression_fail_clipped_audio.mp4", 1.12, "full", 8.0),
        ("regression_fail_silent_audio.mp4", 1.12, "full", 0.0),
        ("regression_fail_partial_cta.mp4", 1.12, "partial", 0.08),
        ("regression_fail_shifted_cta.mp4", 1.12, "shifted", 0.08),
        ("regression_fail_patch_and_cta.mp4", 1.05, "none", 0.08),
    ]
    cases = demo_cases if args.demo_only else [*demo_cases, *regression_cases]
    for filename, punch_scale, cta_mode, volume in cases:
        generate(
            filename,
            punch_scale=punch_scale,
            cta_mode=cta_mode,
            volume=volume,
        )


if __name__ == "__main__":
    main()
