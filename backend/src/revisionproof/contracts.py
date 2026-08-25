from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutionMode(StrEnum):
    LIVE = "LIVE"
    FIXTURE = "FIXTURE"
    OFFLINE_REHEARSAL = "OFFLINE_REHEARSAL"
    UNAVAILABLE = "UNAVAILABLE"


class RunState(StrEnum):
    INDEXED = "INDEXED"
    NOTES_PARSED = "NOTES_PARSED"
    EVIDENCE_ANCHORED = "EVIDENCE_ANCHORED"
    PREVIEWS_READY = "PREVIEWS_READY"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    VERSION_UPLOADED = "VERSION_UPLOADED"
    VERIFYING = "VERIFYING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    FAILED = "FAILED"


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    NOT_CHECKED = "NOT_CHECKED"


class PatchType(StrEnum):
    PUNCH_IN = "PUNCH_IN"


class TimeRange(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_order(self) -> TimeRange:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        return self


class DemoAsset(BaseModel):
    asset_id: str
    title: str
    source_url: str
    duration_seconds: float
    width: int
    height: int
    codec: str


class EvidenceAnchor(BaseModel):
    segment_id: str = Field(min_length=1, max_length=128)
    time_range: TimeRange
    score: float = Field(ge=0, le=1)
    transcript: str = Field(max_length=4000)
    visual_summary: str = Field(max_length=2000)
    source: Literal["fixture.segment_index", "mcp-clickhouse.run_query"]


class ParsedFeedback(BaseModel):
    raw_text: str = Field(min_length=1, max_length=2000)
    intent: str = Field(min_length=1, max_length=500)
    patch_type: PatchType = PatchType.PUNCH_IN
    target_phrase: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=1000)
    interpreter_source: Literal["fixture.interpreter", "google.vertex.gemini"]


class PatchCandidate(BaseModel):
    candidate_id: Literal["A", "B"]
    patch_type: PatchType = PatchType.PUNCH_IN
    scale: Literal[1.05, 1.12]
    time_range: TimeRange
    preview_url: str | None = None


class LockedElement(BaseModel):
    element_id: str
    kind: Literal["CTA_OVERLAY", "AUDIO"]
    time_range: TimeRange
    description: str


class RevisionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["2.0"] = "2.0"
    run_id: str
    asset_id: str
    approved_candidate: PatchCandidate
    evidence: tuple[EvidenceAnchor, ...]
    locked_elements: tuple[LockedElement, ...]
    approved_at: datetime
    spec_hash: str

    @classmethod
    def freeze(
        cls,
        *,
        run_id: str,
        asset_id: str,
        candidate: PatchCandidate,
        evidence: list[EvidenceAnchor],
        locked_elements: list[LockedElement],
        approved_at: datetime | None = None,
    ) -> RevisionSpec:
        timestamp = approved_at or datetime.now(UTC)
        payload: dict[str, Any] = {
            "schema_version": "2.0",
            "run_id": run_id,
            "asset_id": asset_id,
            "approved_candidate": candidate.model_dump(mode="json"),
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "locked_elements": [item.model_dump(mode="json") for item in locked_elements],
            "approved_at": timestamp.isoformat().replace("+00:00", "Z"),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return cls(**payload, spec_hash=hashlib.sha256(canonical.encode()).hexdigest())


class VerificationCheck(BaseModel):
    check_id: Literal["approved_patch", "locked_cta", "locked_audio"]
    label: str
    verdict: Verdict
    failure_code: str | None = None
    measured: dict[str, float | str | int]
    threshold: dict[str, float | str | int]
    evidence_time_range: TimeRange


class VerificationProof(BaseModel):
    version_label: str
    spec_hash: str
    verdict: Verdict
    publish_allowed: bool
    checks: list[VerificationCheck]
    generated_at: datetime


class RunEvent(BaseModel):
    sequence: int
    state: RunState
    message: str
    occurred_at: datetime


class RunSnapshot(BaseModel):
    run_id: str
    asset: DemoAsset
    mode: ExecutionMode
    state: RunState
    feedback: ParsedFeedback | None = None
    evidence: list[EvidenceAnchor] = Field(default_factory=list)
    candidates: list[PatchCandidate] = Field(default_factory=list)
    spec: RevisionSpec | None = None
    proof: VerificationProof | None = None
    events: list[RunEvent] = Field(default_factory=list)
    error: str | None = None


class CreateRunRequest(BaseModel):
    asset_id: str
    feedback: str = Field(min_length=8, max_length=2000)


class ApprovalRequest(BaseModel):
    candidate_id: Literal["A", "B"]
