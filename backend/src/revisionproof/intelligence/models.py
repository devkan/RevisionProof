from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from revisionproof.editing.models import EditPlan

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
    kind: Literal["zoom", "recipe"] = "zoom"
    intent: str
    target_phrase: str
    candidate_id: Literal["A", "B"] | None = None
    scale: Literal[1.05, 1.12] | None = None
    duration_seconds: float = Field(ge=0.1, le=60.05)
    edit_plan: EditPlan | None = None
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


class SceneSearchHit(BaseModel):
    segment_id: str = Field(min_length=26, max_length=26)
    start_seconds: float = Field(ge=0, le=60)
    end_seconds: float = Field(gt=0, le=60.05)
    score: float = Field(ge=-1, le=1)
    transcript: str = Field(default="", max_length=4000)
    visual_summary: str = Field(min_length=1, max_length=1000)


class SceneSearchResult(BaseModel):
    search_id: str = Field(min_length=26, max_length=26)
    asset_id: str = Field(min_length=26, max_length=26)
    query: str = Field(min_length=2, max_length=500)
    source: Literal["fixture.scene_search", "mcp-clickhouse.run_query"]
    segments_indexed: int = Field(ge=1, le=15)
    matches: list[SceneSearchHit] = Field(default_factory=list, max_length=3)
    message: str
