from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from revisionproof.intelligence.models import EditMemorySearch, RevisionChangeMap


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


class SafetyClassification(StrEnum):
    AUTO_PREVIEWABLE = "AUTO_PREVIEWABLE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    MANUAL_CREATIVE = "MANUAL_CREATIVE"


class TimeRange(BaseModel):
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float = Field(gt=0, allow_inf_nan=False)

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
    source_kind: Literal["demo", "upload"] = "demo"


class EvidenceAnchor(BaseModel):
    segment_id: str = Field(min_length=1, max_length=128)
    time_range: TimeRange
    score: float = Field(ge=0, le=1)
    transcript: str = Field(max_length=4000)
    visual_summary: str = Field(max_length=2000)
    source: Literal["fixture.segment_index", "mcp-clickhouse.run_query", "user.selected_range"]


class ParsedFeedback(BaseModel):
    raw_text: str = Field(min_length=1, max_length=2000)
    intent: str = Field(min_length=1, max_length=500)
    patch_type: PatchType = PatchType.PUNCH_IN
    target_phrase: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=1000)
    interpreter_source: Literal["fixture.interpreter", "google.vertex.gemini", "local.range_rules"]


class RevisionNote(BaseModel):
    note_id: str = Field(min_length=1, max_length=64)
    raw_text: str = Field(min_length=1, max_length=2000)
    intent: str = Field(min_length=1, max_length=500)
    classification: SafetyClassification
    confidence: float = Field(ge=0, le=1)
    target_phrase: str | None = Field(default=None, max_length=200)
    rationale: str = Field(min_length=1, max_length=1000)
    clarification_question: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_safety_boundary(self) -> RevisionNote:
        if self.classification is SafetyClassification.AUTO_PREVIEWABLE:
            if self.confidence < 0.82 or not self.target_phrase:
                raise ValueError("AUTO_PREVIEWABLE requires confidence >= 0.82 and a target")
            if self.clarification_question:
                raise ValueError("AUTO_PREVIEWABLE must not include a clarification question")
        elif self.classification is SafetyClassification.NEEDS_CLARIFICATION:
            if not 0.55 <= self.confidence < 0.82 or not self.clarification_question:
                raise ValueError("NEEDS_CLARIFICATION requires confidence 0.55-0.82 and a question")
        elif self.target_phrase is not None or self.clarification_question is not None:
            raise ValueError("MANUAL_CREATIVE must not enter the automated target flow")
        return self


class PatchCandidate(BaseModel):
    candidate_id: Literal["A", "B"]
    patch_type: PatchType = PatchType.PUNCH_IN
    scale: Literal[1.05, 1.12]
    time_range: TimeRange
    preview_url: str | None = None

    @model_validator(mode="after")
    def validate_preview_duration(self) -> PatchCandidate:
        duration = self.time_range.end_seconds - self.time_range.start_seconds
        if not 4 <= duration <= 8:
            raise ValueError("PUNCH_IN preview duration must be between 4 and 8 seconds")
        return self


class LockedElement(BaseModel):
    element_id: str
    kind: Literal["CTA_OVERLAY", "VIDEO_CONTENT", "AUDIO"]
    time_range: TimeRange
    description: str


class VerificationManifest(BaseModel):
    check_id: Literal["approved_patch", "locked_cta", "locked_audio"]
    required: Literal[True] = True
    time_range: TimeRange
    roi: tuple[int, int, int, int] | None = None
    threshold: dict[str, float]

    @model_validator(mode="after")
    def validate_check_contract(self) -> VerificationManifest:
        expected_keys = {
            "approved_patch": {
                "minimum_similarity",
                "minimum_winner_margin",
                "minimum_passing_ratio",
            },
            "locked_cta": {"minimum_frame_similarity", "minimum_passing_ratio"},
            "locked_audio": {"maximum_rms_delta_db", "maximum_peak_dbfs"},
        }
        relative_audio = self.check_id == "locked_audio" and set(self.threshold) == {
            "maximum_rms_delta_db",
            "maximum_peak_delta_db",
        }
        if not relative_audio and set(self.threshold) != expected_keys[self.check_id]:
            raise ValueError(f"{self.check_id} threshold keys do not match the check contract")
        ratio_keys = {
            "minimum_similarity",
            "minimum_passing_ratio",
            "minimum_frame_similarity",
        }
        if any(not 0 <= value <= 1 for key, value in self.threshold.items() if key in ratio_keys):
            raise ValueError("similarity and ratio thresholds must be between zero and one")
        if self.threshold.get("minimum_winner_margin", 0) < 0:
            raise ValueError("winner margin must be non-negative")
        if self.threshold.get("maximum_rms_delta_db", 0) < 0:
            raise ValueError("RMS tolerance must be non-negative")
        if not 0 <= self.threshold.get("maximum_peak_delta_db", 0) <= 0.1:
            raise ValueError("peak preservation tolerance must be between 0 and 0.1 dB")
        if self.threshold.get("maximum_peak_dbfs", 0) > 0:
            raise ValueError("peak limit must be at or below 0 dBFS")
        if self.check_id == "locked_cta":
            if (
                self.roi is None
                or any(value < 0 for value in self.roi[:2])
                or any(value <= 0 for value in self.roi[2:])
            ):
                raise ValueError("locked_cta requires a positive ROI")
        elif self.roi is not None:
            raise ValueError(f"{self.check_id} must not define an ROI")
        return self


class RevisionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["2.0", "2.1", "2.2"] = "2.0"
    run_id: str
    asset_id: str
    approved_candidate: PatchCandidate
    evidence: tuple[EvidenceAnchor, ...]
    locked_elements: tuple[LockedElement, ...]
    verification_manifest: tuple[VerificationManifest, ...]
    approved_at: datetime
    spec_hash: str

    @model_validator(mode="after")
    def validate_integrity(self) -> RevisionSpec:
        check_ids = [item.check_id for item in self.verification_manifest]
        if sorted(check_ids) != ["approved_patch", "locked_audio", "locked_cta"]:
            raise ValueError("verification_manifest must freeze exactly three unique checks")
        if self.manifest_for("approved_patch").time_range != self.approved_candidate.time_range:
            raise ValueError("approved patch manifest must match the approved candidate range")
        locked_by_kind = {element.kind: element for element in self.locked_elements}
        visual_kind = "VIDEO_CONTENT" if self.schema_version != "2.0" else "CTA_OVERLAY"
        relative_audio = "maximum_peak_delta_db" in self.manifest_for("locked_audio").threshold
        if relative_audio != (self.schema_version == "2.2"):
            raise ValueError("relative audio preservation requires spec 2.2")
        if len(self.locked_elements) != 2 or set(locked_by_kind) != {visual_kind, "AUDIO"}:
            raise ValueError("RevisionSpec must freeze exactly one visual and one audio lock")
        if (
            self.manifest_for("locked_cta").time_range != locked_by_kind[visual_kind].time_range
            or self.manifest_for("locked_audio").time_range != locked_by_kind["AUDIO"].time_range
        ):
            raise ValueError("verification manifest ranges must match locked elements")
        payload = self.model_dump(mode="json", exclude={"spec_hash"})
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        expected_hash = hashlib.sha256(canonical.encode()).hexdigest()
        if self.spec_hash != expected_hash:
            raise ValueError("RevisionSpec hash does not match its canonical content")
        return self

    def manifest_for(
        self, check_id: Literal["approved_patch", "locked_cta", "locked_audio"]
    ) -> VerificationManifest:
        return next(item for item in self.verification_manifest if item.check_id == check_id)

    @classmethod
    def freeze(
        cls,
        *,
        run_id: str,
        asset_id: str,
        candidate: PatchCandidate,
        evidence: list[EvidenceAnchor],
        locked_elements: list[LockedElement],
        verification_manifest: list[VerificationManifest],
        approved_at: datetime | None = None,
    ) -> RevisionSpec:
        timestamp = approved_at or datetime.now(UTC)
        payload: dict[str, Any] = {
            "schema_version": "2.2"
            if any("maximum_peak_delta_db" in m.threshold for m in verification_manifest)
            else "2.1"
            if any(e.kind == "VIDEO_CONTENT" for e in locked_elements)
            else "2.0",
            "run_id": run_id,
            "asset_id": asset_id,
            "approved_candidate": candidate.model_dump(mode="json"),
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "locked_elements": [item.model_dump(mode="json") for item in locked_elements],
            "verification_manifest": [
                item.model_dump(mode="json") for item in verification_manifest
            ],
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
    evidence_urls: list[str] = Field(default_factory=list)


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
    selected_range: TimeRange | None = None
    mode: ExecutionMode
    state: RunState
    notes: list[RevisionNote] = Field(default_factory=list)
    selected_note_id: str | None = Field(default=None, max_length=64)
    feedback: ParsedFeedback | None = None
    evidence: list[EvidenceAnchor] = Field(default_factory=list)
    candidates: list[PatchCandidate] = Field(default_factory=list)
    spec: RevisionSpec | None = None
    proof: VerificationProof | None = None
    generated_version_url: str | None = None
    change_map: RevisionChangeMap | None = None
    edit_memory: EditMemorySearch | None = None
    memory_saved: bool = False
    delivery_approved: bool = False
    retryable: bool = False
    events: list[RunEvent] = Field(default_factory=list)
    error: str | None = None
    source_feedback: str | None = Field(default=None, exclude=True)


class CreateRunRequest(BaseModel):
    asset_id: str
    feedback: str = Field(min_length=8, max_length=2000)


class ApprovalRequest(BaseModel):
    candidate_id: Literal["A", "B"]


class PreviewRequest(BaseModel):
    note_id: str = Field(min_length=1, max_length=64)
