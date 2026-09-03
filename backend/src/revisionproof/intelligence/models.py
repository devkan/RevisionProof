from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SearchEngine = Literal["exact", "hnsw", "qbit"]


class MemoryAuthorizationError(PermissionError):
    """A missing/invalid owner key, not an operating-system permission failure."""


class ChangeWindow(BaseModel):
    second: int = Field(ge=0, le=599)
    sample_count: int = Field(ge=1, le=4)
    visual_delta: float = Field(ge=0, le=1)
    residual_delta: float = Field(ge=0, le=1)
    cta_delta: float = Field(ge=0, le=1)
    audio_delta_db: float = Field(ge=0)
    requested: bool
    status: Literal["requested", "unchanged", "review"]


class RevisionChangeMap(BaseModel):
    status: Literal["ready", "unavailable"]
    version_label: str
    spec_hash: str
    analysis_id: str
    source: Literal["fixture.frame_analysis", "mcp-clickhouse.run_query"]
    sample_fps: int = 2
    duration_seconds: float
    windows: list[ChangeWindow] = Field(default_factory=list)
    message: str


class ApprovedEditMatch(BaseModel):
    memory_id: str
    intent: str
    target_phrase: str
    candidate_id: Literal["A", "B"]
    scale: Literal[1.05, 1.12]
    duration_seconds: float = Field(ge=4, le=8)
    similarity: float = Field(ge=-1, le=1)
    approved_at: datetime
    spec_hash: str


class EditMemorySearch(BaseModel):
    status: Literal["ready", "empty", "unavailable", "disabled"]
    requested_engine: SearchEngine = "hnsw"
    actual_engine: Literal["exact", "hnsw", "qbit", "fixture", "unavailable", "none"]
    source: Literal["fixture.approved_memory", "mcp-clickhouse.run_query"]
    collection_size: int = Field(default=0, ge=0)
    elapsed_ms: float = Field(default=0, ge=0)
    precision_bits: int | None = None
    index_verified: bool = False
    matches: list[ApprovedEditMatch] = Field(default_factory=list)
    message: str


class MemorySaveResult(BaseModel):
    memory_id: str
    status: Literal["saved", "already_saved"]
    source: Literal["fixture.approved_memory", "clickhouse.approved_memory"]
