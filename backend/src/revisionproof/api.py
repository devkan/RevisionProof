from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, StreamingResponse
from starlette.types import Receive, Scope, Send

from revisionproof.assets import list_demo_assets
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    PreviewRequest,
    RevisionSpec,
    RunSnapshot,
    RunState,
    TimeRange,
    VerificationProof,
)
from revisionproof.editing.models import (
    EditInterpretation,
    EditPlan,
    InterpretEditRequest,
    LogoAsset,
    TranscriptionLanguage,
    TranscriptionResult,
)
from revisionproof.intelligence.models import (
    EditMemorySearch,
    MemoryAuthorizationError,
    MemorySaveResult,
    SearchEngine,
)
from revisionproof.media.source import SourceUploadError
from revisionproof.repository import RunCapacityBusyError, RunNotFoundError
from revisionproof.service import RateLimitError, RevisionProofService

router = APIRouter(prefix="/api")


class ActiveLeaseStreamingResponse(StreamingResponse):
    def __init__(
        self,
        *args: Any,
        release: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        self._release = release
        super().__init__(*args, **kwargs)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            self._release()


def get_service(request: Request) -> RevisionProofService:
    return request.app.state.service


ServiceDep = Annotated[RevisionProofService, Depends(get_service)]


def as_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SourceUploadError):
        return HTTPException(status_code=exc.status_code, detail=str(exc))
    if isinstance(exc, MemoryAuthorizationError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, RunNotFoundError):
        return HTTPException(status_code=404, detail="run not found")
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, RateLimitError):
        return HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    if isinstance(exc, RunCapacityBusyError):
        return HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    if isinstance(exc, ValueError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="internal processing error")


@router.get("/runtime")
def runtime_status(service: ServiceDep):
    mode = service.settings.mode
    return {
        "mode": mode,
        "mutable": mode in {ExecutionMode.LIVE, ExecutionMode.FIXTURE},
        "live_ready": mode is ExecutionMode.LIVE and not service.settings.live_missing_settings,
        "missing_settings": service.settings.live_missing_settings,
        "intelligence_enabled": service.settings.intelligence_enabled,
        "upload_limits": {
            "max_bytes": service.settings.max_upload_bytes,
            "max_duration_seconds": service.settings.max_duration_seconds,
            "min_duration_seconds": 4,
        },
        "logo_limits": {
            "max_bytes": service.settings.max_logo_bytes,
            "max_dimension": 2048,
        },
        "memory_save_policy": (
            "operator_key"
            if mode is ExecutionMode.LIVE and service.settings.memory_write_token
            else "local_rehearsal"
            if mode is ExecutionMode.FIXTURE
            else "read_only"
        ),
        "message": (
            "Live integrations are configured; successful calls are proven per run"
            if mode is ExecutionMode.LIVE and not service.settings.live_missing_settings
            else "Deterministic development fixtures; not live evidence"
            if mode is ExecutionMode.FIXTURE
            else "Recorded rehearsal is read-only"
            if mode is ExecutionMode.OFFLINE_REHEARSAL
            else "Required integrations are unavailable"
        ),
    }


@router.get("/demo-assets")
def demo_assets(service: ServiceDep):
    return list_demo_assets(service.settings.runtime_dir, service.executor)


@router.post("/edit-assets/logo", response_model=LogoAsset, status_code=201)
def upload_logo(
    service: ServiceDep,
    file: Annotated[UploadFile, File()],
    content_sha256: Annotated[str | None, Header(alias="X-Content-SHA256")] = None,
) -> LogoAsset:
    if file.content_type not in {
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/octet-stream",
    }:
        raise HTTPException(status_code=415, detail="Choose a PNG, JPG, or WebP logo.")
    try:
        size = file.size
        if size is None:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        return service.upload_logo(
            file.file,
            size=size,
            content_sha256=content_sha256 or "",
        )
    except Exception as exc:
        raise as_http_error(exc) from exc
    finally:
        file.file.close()


@router.post("/transcriptions", response_model=TranscriptionResult)
async def transcribe_source(
    service: ServiceDep,
    language: Annotated[TranscriptionLanguage, Form()],
    file: Annotated[UploadFile | None, File()] = None,
    asset_id: Annotated[str | None, Form(max_length=64)] = None,
    content_sha256: Annotated[str | None, Header(alias="X-Content-SHA256")] = None,
) -> TranscriptionResult:
    if file is not None and file.content_type not in {
        "video/mp4",
        "application/mp4",
        "video/quicktime",
        "video/webm",
        "application/octet-stream",
    }:
        raise HTTPException(status_code=415, detail="Choose an MP4, MOV, or WebM video.")
    if file is not None and asset_id:
        raise HTTPException(status_code=409, detail="Choose either your video or the sample.")
    try:
        size = file.size if file is not None else 0
        if file is not None and size is None:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        return await service.transcribe_source(
            language=language,
            stream=file.file if file is not None else None,
            size=size or 0,
            content_sha256=content_sha256 or "",
            asset_id=asset_id,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc
    finally:
        if file is not None:
            await file.close()


@router.post("/edit-plans/interpret", response_model=EditInterpretation)
async def interpret_edit_plan(payload: InterpretEditRequest, service: ServiceDep):
    try:
        return await service.interpret_edit_plan(payload)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs", response_model=RunSnapshot, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: CreateRunRequest,
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return await service.create_run(payload, idempotency_key)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/upload", response_model=RunSnapshot, status_code=201)
async def upload_source(
    file: Annotated[UploadFile, File()],
    feedback: Annotated[str, Form(min_length=2, max_length=2000)],
    start_seconds: Annotated[float, Form(ge=0)],
    end_seconds: Annotated[float, Form(gt=0)],
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    content_sha256: Annotated[str | None, Header(alias="X-Content-SHA256")] = None,
    edit_plan: Annotated[str | None, Form(max_length=24000)] = None,
) -> RunSnapshot:
    try:
        if file.content_type not in {
            "video/mp4",
            "application/mp4",
            "video/quicktime",
            "video/webm",
            "application/octet-stream",
        }:
            raise SourceUploadError("Choose an MP4, MOV, or WebM video.", 415)
        return await service.create_uploaded_run(
            stream=file.file,
            size=file.size or 0,
            filename=file.filename or "Uploaded video",
            feedback=feedback,
            selected_range=TimeRange(start_seconds=start_seconds, end_seconds=end_seconds),
            content_sha256=content_sha256 or "",
            idempotency_key=idempotency_key,
            edit_plan=EditPlan.model_validate_json(edit_plan) if edit_plan else None,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc
    finally:
        await file.close()


@router.get("/runs/{run_id}/source-video")
def source_video(run_id: str, service: ServiceDep):
    try:
        snapshot = service.repository.get(run_id)
        if snapshot.asset.source_kind != "upload":
            raise ValueError("This run uses the sample video")
        return FileResponse(
            service.repository.source_path(run_id),
            media_type="video/mp4",
            headers={"Cache-Control": "private, no-store"},
        )
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}", response_model=RunSnapshot)
def get_run(run_id: str, service: ServiceDep) -> RunSnapshot:
    try:
        return service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/retry", response_model=RunSnapshot)
async def retry_run(
    run_id: str,
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return await service.retry_live_interpretation(run_id, idempotency_key)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}/events")
def get_run_events(run_id: str, request: Request, service: ServiceDep):
    try:
        service.repository.acquire_active(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc

    async def stream() -> AsyncIterator[str]:
        terminal_states = {RunState.BLOCKED, RunState.READY, RunState.FAILED}
        last_event_id = request.headers.get("last-event-id", "0")
        try:
            cursor = max(0, int(last_event_id))
        except ValueError:
            cursor = 0
        idle_ticks = 0
        yield "retry: 1000\n\n"
        while idle_ticks < 60:
            snapshot = service.repository.get(run_id)
            if cursor < len(snapshot.events):
                for event in snapshot.events[cursor:]:
                    yield (
                        f"id: {event.sequence}\n"
                        "event: run_state\n"
                        "data: " + event.model_dump_json() + "\n\n"
                    )
                cursor = len(snapshot.events)
                idle_ticks = 0
                if snapshot.events and snapshot.events[-1].state in terminal_states:
                    return
            else:
                yield ": keep-alive\n\n"
                idle_ticks += 1
            await asyncio.sleep(1)

    return ActiveLeaseStreamingResponse(
        stream(),
        release=lambda: service.repository.release_active(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/runs/{run_id}/previews", response_model=RunSnapshot)
def create_previews(
    run_id: str,
    service: ServiceDep,
    payload: PreviewRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return service.generate_previews(
            run_id,
            idempotency_key,
            selected_note_id=payload.note_id if payload else None,
            edit_plan=payload.edit_plan if payload else None,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/approvals", response_model=RunSnapshot)
def approve(
    run_id: str,
    payload: ApprovalRequest,
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return service.approve(run_id, payload, idempotency_key)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/automatic-version", response_model=RunSnapshot)
def render_approved_version(
    run_id: str,
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return service.render_approved_version(run_id, idempotency_key)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}/generated-video")
def generated_video(run_id: str, service: ServiceDep):
    try:
        snapshot = service.repository.get(run_id)
        if snapshot.generated_version_url is None:
            raise FileNotFoundError("generated video is not available")
        path = service.repository.version_path(run_id)
        if not path.is_file():
            raise FileNotFoundError("generated video is not available")
        return FileResponse(
            path,
            media_type="video/mp4",
            filename=f"revisionproof-{run_id[-8:]}.mp4",
            content_disposition_type="inline",
        )
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
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    content_sha256: Annotated[str | None, Header(alias="X-Content-SHA256")] = None,
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
            idempotency_key=idempotency_key,
            content_sha256=content_sha256,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc
    finally:
        file.file.close()


@router.post("/runs/{run_id}/demo-versions/{version_label}", response_model=RunSnapshot)
def verify_demo_version(
    run_id: str,
    version_label: str,
    service: ServiceDep,
) -> RunSnapshot:
    try:
        return service.verify_demo_version(
            run_id=run_id,
            version_label=version_label,
        )
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.get("/runs/{run_id}/proof", response_model=VerificationProof)
def get_proof(run_id: str, service: ServiceDep):
    try:
        snapshot = service.repository.get(run_id)
    except Exception as exc:
        raise as_http_error(exc) from exc
    if snapshot.proof is None:
        raise HTTPException(status_code=404, detail="verification proof not available")
    return snapshot.proof


@router.get("/runs/{run_id}/edit-memory", response_model=EditMemorySearch)
def search_edit_memory(run_id: str, service: ServiceDep, engine: SearchEngine = "hnsw"):
    try:
        return service.search_memory(run_id, engine)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/edit-memory", response_model=MemorySaveResult)
def save_edit_memory(
    run_id: str,
    service: ServiceDep,
    workspace_key: Annotated[str | None, Header(alias="X-Workspace-Key")] = None,
):
    try:
        return service.save_memory(run_id, workspace_key)
    except Exception as exc:
        raise as_http_error(exc) from exc


@router.post("/runs/{run_id}/delivery-approval", response_model=RunSnapshot)
def approve_for_delivery(
    run_id: str,
    service: ServiceDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunSnapshot:
    try:
        return service.approve_for_delivery(run_id, idempotency_key)
    except Exception as exc:
        raise as_http_error(exc) from exc
