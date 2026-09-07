from __future__ import annotations

from pathlib import Path

from revisionproof.contracts import DemoAsset
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import probe_media

DEMO_ASSET_ID = "01M00000000000000000000000"


def demo_asset_path(runtime_dir: Path) -> Path:
    return runtime_dir / "demo" / "revisionproof_v1.mp4"


def list_demo_assets(runtime_dir: Path, executor: MediaExecutor) -> list[DemoAsset]:
    path = demo_asset_path(runtime_dir)
    if not path.exists():
        return []
    info = probe_media(path, executor)
    return [
        DemoAsset(
            asset_id=DEMO_ASSET_ID,
            title="RevisionProof — Product Reveal",
            source_url="/media/demo/revisionproof_v1.mp4",
            duration_seconds=round(info.duration_seconds, 3),
            width=info.width,
            height=info.height,
            codec=f"{info.video_codec}/{info.audio_codec}",
        )
    ]


def require_demo_asset(
    asset_id: str, runtime_dir: Path, executor: MediaExecutor
) -> tuple[DemoAsset, Path]:
    asset = next(
        (item for item in list_demo_assets(runtime_dir, executor) if item.asset_id == asset_id),
        None,
    )
    if asset is None:
        raise FileNotFoundError("demo asset is missing; run scripts/generate_demo_assets.py")
    return asset, demo_asset_path(runtime_dir)
