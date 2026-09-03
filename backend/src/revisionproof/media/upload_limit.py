from collections import deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class UploadBodyLimit:
    """Reject oversized multipart bodies before the framework spools the file."""

    def __init__(self, app: ASGIApp, max_file_bytes: int):
        self.app = app
        self.max_file_bytes = max_file_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        upload = path == "/api/runs/upload" or (
            path.startswith("/api/runs/") and path.endswith("/versions")
        )
        if scope["type"] != "http" or scope.get("method") != "POST" or not upload:
            await self.app(scope, receive, send)
            return
        limit = self.max_file_bytes + 64 * 1024  # bounded form fields + multipart envelope
        response = JSONResponse(
            status_code=413,
            content={
                "detail": (
                    f"Video is too large. Maximum: {self.max_file_bytes // 1048576} MiB. "
                    "Choose a smaller file."
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
