from __future__ import annotations

import subprocess
import threading
from pathlib import Path


class MediaCommandError(RuntimeError):
    pass


class MediaExecutor:
    """Runs one fixed-array FFmpeg/FFprobe command at a time."""

    def __init__(self, timeout_seconds: int = 90) -> None:
        self.timeout_seconds = timeout_seconds
        self._lock = threading.Lock()

    def run(self, args: list[str], *, expected_output: Path | None = None) -> str:
        allowed_commands = {"ffmpeg", "ffmpeg.exe", "ffprobe", "ffprobe.exe"}
        if not args or Path(args[0]).name.lower() not in allowed_commands:
            raise ValueError("media executor only accepts ffmpeg or ffprobe")
        with self._lock:
            try:
                result = subprocess.run(
                    args,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                if expected_output and expected_output.exists():
                    expected_output.unlink()
                detail = getattr(exc, "stderr", None) or str(exc)
                raise MediaCommandError(detail[-2000:]) from exc
        if expected_output is not None and not expected_output.exists():
            raise MediaCommandError(f"expected output was not created: {expected_output}")
        return result.stdout
