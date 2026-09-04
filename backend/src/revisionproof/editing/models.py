"""Original-time edit plans with deterministic output-timeline mapping."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EditOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["zoom", "text", "subtitle", "cut", "remove_silence", "speed", "volume", "logo"]
    start: float = Field(ge=0, le=60, allow_inf_nan=False)
    # Vertex response_schema does not support exclusiveMinimum. The duration
    # validator below still requires end >= start + 0.09 (and start >= 0).
    end: float = Field(ge=0, le=60.05, allow_inf_nan=False)
    text: str = Field(default="", max_length=160)
    position: Literal[
        "top", "center", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"
    ] = "bottom"
    threshold_db: float = Field(default=-40, ge=-60, le=-20, allow_inf_nan=False)
    min_silence: float = Field(default=0.7, ge=0.3, le=3, allow_inf_nan=False)
    detected: bool = False
    rate: float = Field(default=1, ge=0.5, le=2, allow_inf_nan=False)
    volume_db: float = Field(default=0, ge=-60, le=12, allow_inf_nan=False)
    asset_id: str = Field(default="", max_length=64)
    asset_sha256: str = Field(default="", max_length=64)

    @model_validator(mode="after")
    def valid_operation(self) -> EditOperation:
        if self.end - self.start < 0.09:
            raise ValueError("Each edit needs at least 0.1 seconds.")
        if self.kind in {"text", "subtitle"}:
            if not self.text.strip():
                raise ValueError("Enter the exact words to display.")
            if any(ord(c) < 32 and c != "\n" for c in self.text):
                raise ValueError("Text contains unsupported control characters.")
            if self.text.count("\n") > 2:
                raise ValueError("Use at most three lines per caption.")
        elif self.text:
            raise ValueError("Only text and subtitle edits accept display text.")
        if self.detected and self.kind != "cut":
            raise ValueError("Only proposed cuts can be marked as detected silence.")
        if self.kind == "speed":
            if abs(self.rate - 1) < 0.001:
                raise ValueError("Choose a speed other than 1×.")
        elif self.rate != 1:
            raise ValueError("Only speed edits accept a playback rate.")
        if self.kind == "volume":
            if abs(self.volume_db) < 0.001:
                raise ValueError("Choose a volume adjustment other than 0 dB.")
        elif self.volume_db != 0:
            raise ValueError("Only volume edits accept a dB adjustment.")
        if self.kind == "logo":
            if not re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", self.asset_id):
                raise ValueError("Choose a valid uploaded logo.")
            if not re.fullmatch(r"[a-f0-9]{64}", self.asset_sha256):
                raise ValueError("The uploaded logo checksum is missing or invalid.")
        elif self.asset_id or self.asset_sha256:
            raise ValueError("Only logo edits accept an uploaded image.")
        return self


class KeptSpan(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_start: float
    source_end: float
    output_start: float
    rate: float = 1

    @property
    def duration(self) -> float:
        return (self.source_end - self.source_start) / self.rate

    @property
    def source_duration(self) -> float:
        return self.source_end - self.source_start


class EditPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_duration: float = Field(ge=1, le=60.05, allow_inf_nan=False)
    operations: tuple[EditOperation, ...] = Field(max_length=24)

    @model_validator(mode="after")
    def valid_plan(self) -> EditPlan:
        if any(op.end > self.source_duration + 0.001 for op in self.operations):
            raise ValueError("An edit extends past the original video. Check its end time.")
        visual = [op for op in self.operations if op.kind in {"zoom", "text", "subtitle", "logo"}]
        for i, a in enumerate(visual):
            for b in visual[i + 1 :]:
                overlaps = max(a.start, b.start) < min(a.end, b.end)
                same_zoom = a.kind == b.kind == "zoom"
                same_overlay = a.kind != "zoom" and b.kind != "zoom" and a.position == b.position
                if overlaps and (same_zoom or same_overlay):
                    raise ValueError("Overlapping zooms or overlays in the same position conflict.")
        for kind in ("speed", "volume"):
            timed = [op for op in self.operations if op.kind == kind]
            for i, a in enumerate(timed):
                if any(max(a.start, b.start) < min(a.end, b.end) for b in timed[i + 1 :]):
                    raise ValueError(f"Overlapping {kind} edits conflict.")
        # Detected cuts are suggestions until the user selects them. Validate the
        # committed operations now, and the whole selection again before rendering.
        if any(op.detected for op in self.operations):
            EditPlan(
                source_duration=self.source_duration,
                operations=tuple(op for op in self.operations if not op.detected),
            )
        else:
            self.validate_selection()
        return self

    def validate_selection(self) -> None:
        if self.output_duration < 1 - 0.001:
            raise ValueError("Keep at least one second of the original video.")
        if self.output_duration > 60.05:
            raise ValueError("The edited video must stay within 60 seconds.")
        for op in self.operations:
            if op.kind not in {"zoom", "text", "subtitle", "logo"}:
                continue
            if not any(
                max(op.start, s.source_start) < min(op.end, s.source_end) for s in self.kept_spans
            ):
                raise ValueError("A visual edit is entirely inside a deleted section.")

    @property
    def kept_spans(self) -> tuple[KeptSpan, ...]:
        cuts = sorted((op.start, op.end) for op in self.operations if op.kind == "cut")
        merged: list[list[float]] = []
        for start, end in cuts:
            if merged and start <= merged[-1][1] + 0.001:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        boundaries = {0.0, self.source_duration}
        for start, end in merged:
            boundaries.update((start, end))
        for op in self.operations:
            if op.kind == "speed":
                boundaries.update((op.start, op.end))
        output = 0.0
        spans: list[KeptSpan] = []
        points = sorted(boundaries)
        for source_start, source_end in zip(points, points[1:], strict=False):
            if source_end - source_start <= 0.001:
                continue
            midpoint = (source_start + source_end) / 2
            if any(start <= midpoint < end for start, end in merged):
                continue
            speed = next(
                (
                    op.rate
                    for op in self.operations
                    if op.kind == "speed" and op.start <= midpoint < op.end
                ),
                1,
            )
            if (
                spans
                and abs(spans[-1].source_end - source_start) <= 0.001
                and abs(spans[-1].rate - speed) <= 0.001
            ):
                previous = spans[-1]
                spans[-1] = KeptSpan(
                    source_start=previous.source_start,
                    source_end=source_end,
                    output_start=previous.output_start,
                    rate=speed,
                )
            else:
                spans.append(
                    KeptSpan(
                        source_start=source_start,
                        source_end=source_end,
                        output_start=output,
                        rate=speed,
                    )
                )
            output += (source_end - source_start) / speed
        return tuple(spans)

    @property
    def output_duration(self) -> float:
        return round(sum(span.duration for span in self.kept_spans), 6)

    @property
    def has_appearance_choices(self) -> bool:
        return any(op.kind in {"zoom", "text", "subtitle", "logo"} for op in self.operations)

    def source_time(self, output_time: float) -> float:
        for span in self.kept_spans:
            if span.output_start <= output_time < span.output_start + span.duration:
                return span.source_start + (output_time - span.output_start) * span.rate
        raise ValueError("Output time is outside the edited video.")

    def is_visual_edit(self, output_time: float) -> bool:
        source_time = self.source_time(output_time)
        return any(
            op.kind in {"zoom", "text", "subtitle", "logo"} and op.start <= source_time < op.end
            for op in self.operations
        )


class InterpretEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=2, max_length=2000)
    duration: float = Field(ge=4, le=60.05, allow_inf_nan=False)
    start: float = Field(default=0, ge=0, allow_inf_nan=False)
    end: float = Field(default=6, gt=0, allow_inf_nan=False)


class EditInterpretation(BaseModel):
    plan: EditPlan
    warnings: list[str] = Field(default_factory=list)
    source: Literal["local.edit_rules", "google.vertex.gemini"]


TranscriptionLanguage = Literal["auto", "ko", "en", "mixed"]


class LogoAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_id: str = Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    preview_url: str
    width: int = Field(gt=0, le=512)
    height: int = Field(gt=0, le=512)


class TranscriptionCue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: float = Field(ge=0, le=60, allow_inf_nan=False)
    end: float = Field(gt=0, le=60.05, allow_inf_nan=False)
    text: str = Field(min_length=1, max_length=160)
    language: Literal["ko", "en", "mixed", "other"]

    @model_validator(mode="after")
    def valid_cue(self) -> TranscriptionCue:
        if self.end - self.start < 0.09:
            raise ValueError("Each subtitle cue needs at least 0.1 seconds.")
        if not self.text.strip():
            raise ValueError("A subtitle cue must contain audible words.")
        if any(ord(c) < 32 and c != "\n" for c in self.text) or self.text.count("\n") > 2:
            raise ValueError("A subtitle cue contains unsupported text.")
        return self


class TranscriptionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    duration: float = Field(ge=1, le=60.05, allow_inf_nan=False)
    requested_language: TranscriptionLanguage
    detected_languages: tuple[Literal["ko", "en", "other"], ...] = Field(max_length=3)
    cues: tuple[TranscriptionCue, ...] = Field(max_length=24)
    warnings: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    source: Literal["google.vertex.gemini"]

    @model_validator(mode="after")
    def valid_timeline(self) -> TranscriptionResult:
        previous_end = 0.0
        for cue in self.cues:
            if cue.end > self.duration + 0.001:
                raise ValueError("A subtitle cue extends past the video.")
            if cue.start < previous_end - 0.001:
                raise ValueError("Automatic subtitle cues overlap.")
            previous_end = cue.end
        return self
