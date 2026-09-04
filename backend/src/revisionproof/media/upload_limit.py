from collections import deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class UploadBodyLimit:
    """Reject oversized multipart bodies before the framework spools the file."""

    def __init__(self, app: ASGIApp, max_file_bytes: int, max_logo_bytes: int = 2 * 1048576):
        self.app = app
        self.max_file_bytes = max_file_bytes
        self.max_logo_bytes = max_logo_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        video_upload = path in {"/api/runs/upload", "/api/transcriptions"} or (
            path.startswith("/api/runs/") and path.endswith("/versions")
        )
        logo_upload = path == "/api/edit-assets/logo"
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or not (video_upload or logo_upload)
        ):
            await self.app(scope, receive, send)
            return
        file_limit = self.max_logo_bytes if logo_upload else self.max_file_bytes
        limit = file_limit + 64 * 1024  # bounded form fields + multipart envelope
        limit_label = (
            f"{file_limit // 1048576} MiB"
            if logo_upload
            else f"{file_limit // 1_000_000} MB"
        )
        response = JSONResponse(
            status_code=413,
            content={
                "detail": (
                    f"{'Logo' if logo_upload else 'Video'} is too large. "
                    f"Maximum: {limit_label}. Choose a smaller file."
                )
            },
        )
        headers = dict(scope.get("headers", []))
        try:
            if int(headers.get(b"content-length", b"0")) > limit:
                await response(scope, receive, send)
                return
        except ValueError:
            pass
        messages = deque()
        total = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            total += len(message.get("body", b""))
            if total > limit:
                await response(scope, receive, send)
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay() -> dict:
            return messages.popleft() if messages else await receive()

        await self.app(scope, replay, send)
