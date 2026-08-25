from __future__ import annotations

import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from revisionproof import __version__
from revisionproof.api import router
from revisionproof.contracts import ExecutionMode
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    app.state.service = RevisionProofService(
        settings,
        InMemoryRunRepository(max_runs=settings.max_in_memory_runs),
    )
    yield


app = FastAPI(
    title="RevisionProof API",
    version=__version__,
    description="Deterministic approval firewall for video revisions",
    lifespan=lifespan,
)
app.include_router(router)

settings = get_settings()
settings.runtime_dir.mkdir(parents=True, exist_ok=True)

PUBLIC_MEDIA_PATTERNS = (
    re.compile(r"demo/revisionproof_(?:v1|v2_blocked|v3_ready)\.mp4"),
    re.compile(r"runs/[0-9A-HJKMNP-TV-Z]{26}/previews/[AB]\.mp4"),
    re.compile(r"runs/[0-9A-HJKMNP-TV-Z]{26}/evidence/[A-Za-z0-9._-]{1,96}\.png"),
)


def resolve_public_media(media_path: str) -> Path:
    if not any(pattern.fullmatch(media_path) for pattern in PUBLIC_MEDIA_PATTERNS):
        raise HTTPException(status_code=404, detail="media not found")
    requested = (settings.runtime_dir / Path(media_path)).resolve()
    if settings.runtime_dir not in requested.parents or not requested.is_file():
        raise HTTPException(status_code=404, detail="media not found")
    return requested


@app.get("/media/{media_path:path}", include_in_schema=False)
def public_media(media_path: str):
    return FileResponse(resolve_public_media(media_path))


@app.get("/healthz", include_in_schema=False)
@app.get("/health")
def healthz():
    return {"status": "ok", "version": __version__, "mode": settings.mode}


@app.get("/readyz", include_in_schema=False)
@app.get("/ready")
def readyz():
    missing = settings.live_missing_settings
    if settings.mode is ExecutionMode.UNAVAILABLE or missing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "mode": settings.mode,
                "missing": missing,
            },
        )
    return {
        "status": "ready",
        "mode": settings.mode,
        "live_credentials_configured": (
            settings.mode is ExecutionMode.LIVE and not settings.live_missing_settings
        ),
        "integration_execution_verified": False,
    }


FRONTEND_DIST = Path(__file__).resolve().parent / "static"


@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str):
    requested = FRONTEND_DIST / full_path
    if full_path and requested.is_file() and FRONTEND_DIST in requested.resolve().parents:
        return FileResponse(requested)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content={"detail": "frontend build missing; run npm run build --prefix frontend"},
    )
