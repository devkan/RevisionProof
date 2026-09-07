FROM node:22-bookworm-slim AS web-builder
WORKDIR /workspace
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm ci --prefix frontend
COPY frontend ./frontend
COPY backend/src ./backend/src
RUN npm run build --prefix frontend

FROM ghcr.io/astral-sh/uv:0.6.14 AS uv

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REVISIONPROOF_RUNTIME_DIR=/app/runtime \
    PORT=8080
RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg ca-certificates fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./backend/
COPY --from=web-builder /workspace/backend/src ./backend/src
ARG REVISIONPROOF_INSTALL_LIVE=true
RUN if [ "${REVISIONPROOF_INSTALL_LIVE}" = "true" ]; then \
      uv sync --project backend --frozen --extra live --no-dev --no-editable; \
    else \
      uv sync --project backend --frozen --no-dev --no-editable; \
    fi
COPY scripts ./scripts
RUN backend/.venv/bin/python scripts/generate_demo_assets.py --demo-only
RUN useradd --create-home --uid 10001 revisionproof \
    && chown -R revisionproof:revisionproof /app
USER revisionproof
LABEL org.opencontainers.image.title="RevisionProof" \
      org.opencontainers.image.description="Deterministic video revision approval firewall" \
      com.kanapp.project="revisionproof" \
      com.kanapp.managed-by="revisionproof-repo"
EXPOSE 8080
CMD ["sh", "-c", "exec backend/.venv/bin/uvicorn revisionproof.main:app --host 0.0.0.0 --port ${PORT}"]
