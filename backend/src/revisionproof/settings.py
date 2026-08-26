from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from revisionproof.contracts import ExecutionMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="REVISIONPROOF_",
        extra="ignore",
    )

    mode: ExecutionMode = ExecutionMode.FIXTURE
    runtime_dir: Path = Path("runtime")
    max_upload_mib: int = Field(default=24, ge=1, le=100)
    max_duration_seconds: int = Field(default=60, ge=1, le=600)
    ffmpeg_timeout_seconds: int = Field(default=90, ge=5, le=600)
    gemini_timeout_seconds: int = Field(default=60, ge=5, le=300)
    mcp_timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_in_memory_runs: int = Field(default=64, ge=1, le=256)
    max_new_runs_per_minute: int = Field(default=12, ge=1, le=60)
    max_verification_attempts_per_run: int = Field(default=6, ge=1, le=20)

    gemini_model: str = "gemini-3.5-flash-lite"
    embedding_model: str = "text-embedding-005"
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    gcs_bucket: str | None = None

    clickhouse_host: str | None = None
    clickhouse_port: int = 8443
    clickhouse_secure: bool = True
    clickhouse_verify: bool = True
    clickhouse_database: str = "revisionproof"
    clickhouse_writer_username: str = "revisionproof_writer_user"
    clickhouse_writer_password: str | None = None
    clickhouse_writer_role: str = "revisionproof_writer"
    clickhouse_mcp_username: str = "revisionproof_mcp_user"
    clickhouse_mcp_password: str | None = None
    clickhouse_mcp_role: str = "revisionproof_mcp_reader"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mib * 1024 * 1024

    @property
    def live_missing_settings(self) -> list[str]:
        if self.mode is not ExecutionMode.LIVE:
            return []
        required = {
            "google_cloud_project": self.google_cloud_project,
            "gcs_bucket": self.gcs_bucket,
            "clickhouse_host": self.clickhouse_host,
            "clickhouse_writer_password": self.clickhouse_writer_password,
            "clickhouse_mcp_password": self.clickhouse_mcp_password,
        }
        return [name for name, value in required.items() if not value]

    @model_validator(mode="after")
    def normalize_runtime_dir(self) -> Settings:
        self.runtime_dir = self.runtime_dir.resolve()
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
