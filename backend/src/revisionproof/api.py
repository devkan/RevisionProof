from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from revisionproof.assets import list_demo_assets
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    RevisionSpec,
    RunSnapshot,
    VerificationProof,
)
from revisionproof.repository import RunNotFoundError
from revisionproof.service import RevisionProofService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> RevisionProofService:
    return request.app.state.service


ServiceDep = Annotated[RevisionProofService, Depends(get_service)]


def as_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, RunNotFoundError):
        return HTTPException(status_code=404, detail="run not found")
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="internal processing error")


@router.get("/demo-assets")
def demo_assets(service: ServiceDep):
    return list_demo_assets(service.settings.runtime_dir, service.executor)


@router.post("/runs", response_model=RunSnapshot, status_code=status.HTTP_201_CREATED)
async def create_run(payload: CreateRunRequest, service: ServiceDep) -> RunSnapshot:
    try:
        return await service.create_run(payload)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}", response_model=RunSnapshot)
def get_run(run_id: str, service: ServiceDep) -> RunSnapshot:
    try:
        return service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}/events")
def get_run_events(run_id: str, service: ServiceDep):
    try:
        service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc

    async def stream() -> AsyncIterator[str]:
        cursor = 0
        idle_ticks = 0
        while idle_ticks < 60:
            snapshot = service.repository.get(run_id)
            if cursor < len(snapshot.events):
                for event in snapshot.events[cursor:]:
                    yield "event: run_state\ndata: " + event.model_dump_json() + "\n\n"
                cursor = len(snapshot.events)
                idle_ticks = 0
            else:
                yield ": keep-alive\n\n"
                idle_ticks += 1
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/runs/{run_id}/previews", response_model=RunSnapshot)
def create_previews(run_id: str, service: ServiceDep) -> RunSnapshot:
    try:
        return service.generate_previews(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/approvals", response_model=RunSnapshot)
def approve(
    run_id: str,
    payload: ApprovalRequest,
    service: ServiceDep,
) -> RunSnapshot:
    try:
        return service.approve(run_id, payload)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}/spec", response_model=RevisionSpec)
def get_spec(run_id: str, service: ServiceDep) -> RevisionSpec:
    try:
        snapshot = service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc
    if snapshot.spec is None:
        raise HTTPException(status_code=404, detail="spec not frozen")
    return snapshot.spec


@router.post("/runs/{run_id}/versions", response_model=RunSnapshot)
def upload_version(
    run_id: str,
    version_label: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    service: ServiceDep,
) -> RunSnapshot:
    if file.content_type not in {"video/mp4", "application/mp4", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="only MP4 uploads are accepted")
    try:
        size = file.size
        if size is None:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        return service.upload_and_verify(
            run_id=run_id,
            version_label=version_label,
            stream=file.file,
            size=size,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc
    finally:
        file.file.close()


@router.get("/runs/{run_id}/proof", response_model=VerificationProof)
def get_proof(run_id: str, service: ServiceDep):
    try:
        snapshot = service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc
    if snapshot.proof is None:
        raise HTTPException(status_code=404, detail="verification proof not available")
    return snapshot.proof
