from __future__ import annotations

from pathlib import Path

from revisionproof.contracts import DemoAsset
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import probe_media

DEMO_ASSET_ID = "01M00000000000000000000000"
KANAPP_ASSET_ID = "01M00000000000000000000001"
DEMO_ASSETS = {
    KANAPP_ASSET_ID: ("kanapp_promo_english_editable_30s.mp4", "KANAPP — English Promo (30s)"),
    DEMO_ASSET_ID: ("revisionproof_v1.mp4", "RevisionProof — Product Reveal"),
}


def demo_asset_path(runtime_dir: Path) -> Path:
    return runtime_dir / "demo" / "revisionproof_v1.mp4"


def list_demo_assets(runtime_dir: Path, executor: MediaExecutor) -> list[DemoAsset]:
    assets = []
    for asset_id, (filename, title) in DEMO_ASSETS.items():
        path = runtime_dir / "demo" / filename
        if not path.is_file():
            continue
        info = probe_media(path, executor)
        assets.append(
            DemoAsset(
                asset_id=asset_id,
                title=title,
                source_url=f"/media/demo/{filename}",
                duration_seconds=round(info.duration_seconds, 3),
                width=info.width,
                height=info.height,
                codec=f"{info.video_codec}/{info.audio_codec}",
            )
        )
    return assets


def require_demo_asset(
    asset_id: str, runtime_dir: Path, executor: MediaExecutor
) -> tuple[DemoAsset, Path]:
    if asset_id not in DEMO_ASSETS:
        raise ValueError("asset is not in the RevisionProof demo allowlist")
    asset = next(
        (item for item in list_demo_assets(runtime_dir, executor) if item.asset_id == asset_id),
        None,
    )
    if asset is None:
        raise FileNotFoundError("demo asset is missing; run scripts/generate_demo_assets.py")
    return asset, runtime_dir / "demo" / DEMO_ASSETS[asset_id][0]
