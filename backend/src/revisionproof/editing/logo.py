"""Bounded logo normalization for deterministic overlay rendering."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

from revisionproof.editing.models import LogoAsset
from revisionproof.ids import new_ulid
from revisionproof.media.source import SourceUploadError


def save_logo(
    stream: BinaryIO,
    destination_root: Path,
    *,
    size: int,
    limit: int,
    expected_hash: str,
) -> LogoAsset:
    if size <= 0 or size > limit:
        raise SourceUploadError(
            f"Logo is too large or empty. Maximum: {limit // 1048576} MiB.", 413
        )
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_hash):
        raise SourceUploadError("The logo checksum is missing. Choose the image again.")
    content = stream.read(limit + 1)
    if not content or len(content) > limit:
        raise SourceUploadError(f"Logo is too large. Maximum: {limit // 1048576} MiB.", 413)
    if hashlib.sha256(content).hexdigest() != expected_hash.lower():
        raise SourceUploadError("The logo upload was incomplete. Choose the image again.")
    destination_root.mkdir(parents=True, exist_ok=True)
    if len(list(destination_root.glob("*.png"))) >= 64:
        raise SourceUploadError("The temporary logo workspace is full. Restart and try again.")
    asset_id = new_ulid()
    incoming = destination_root / f".{asset_id}.upload"
    destination = destination_root / f"{asset_id}.png"
    incoming.write_bytes(content)
    try:
        try:
            with Image.open(incoming) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"}:
                    raise SourceUploadError("Choose a PNG, JPG, or WebP logo.", 415)
                if getattr(source, "is_animated", False):
                    raise SourceUploadError("Animated logos are not supported. Choose one image.")
                if not (1 <= source.width <= 2048 and 1 <= source.height <= 2048):
                    raise SourceUploadError("Logo dimensions must be 1–2048 pixels per side.")
                image = ImageOps.exif_transpose(source).convert("RGBA")
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                image.save(destination, "PNG", optimize=True)
        except (UnidentifiedImageError, OSError) as exc:
            raise SourceUploadError("This logo image could not be read.", 415) from exc
        with destination.open("rb") as output:
            digest = hashlib.file_digest(output, "sha256").hexdigest()
        with Image.open(destination) as normalized:
            width, height = normalized.size
        return LogoAsset(
            asset_id=asset_id,
            sha256=digest,
            preview_url=f"/media/edit-assets/{asset_id}.png",
            width=width,
            height=height,
        )
    finally:
        incoming.unlink(missing_ok=True)
        if destination.exists() and destination.stat().st_size > limit:
            destination.unlink()
            raise SourceUploadError("The normalized logo exceeds the size limit.", 413)
