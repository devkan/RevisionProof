from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
    app.state.service = RevisionProofService(settings, InMemoryRunRepository())
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
app.mount("/media", StaticFiles(directory=settings.runtime_dir), name="media")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": __version__, "mode": settings.mode}


@app.get("/readyz")
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
    return {"status": "ready", "mode": settings.mode, "live_verified": False}


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
