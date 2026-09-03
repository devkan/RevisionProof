"""Original-time edit plans. Output time is derived solely from approved kept spans."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EditOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["zoom", "text", "subtitle", "cut", "remove_silence"]
    start: float = Field(ge=0, le=60, allow_inf_nan=False)
    # Vertex response_schema does not support exclusiveMinimum. The duration
    # validator below still requires end >= start + 0.09 (and start >= 0).
    end: float = Field(ge=0, le=60.05, allow_inf_nan=False)
    text: str = Field(default="", max_length=160)
    position: Literal["top", "center", "bottom", "bottom_right"] = "bottom"
    threshold_db: float = Field(default=-40, ge=-60, le=-20, allow_inf_nan=False)
    min_silence: float = Field(default=0.7, ge=0.3, le=3, allow_inf_nan=False)
    detected: bool = False

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
        return self


class KeptSpan(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_start: float
    source_end: float
    output_start: float

    @property
    def duration(self) -> float:
        return self.source_end - self.source_start


class EditPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_duration: float = Field(ge=1, le=60.05, allow_inf_nan=False)
    operations: tuple[EditOperation, ...] = Field(max_length=24)

    @model_validator(mode="after")
    def valid_plan(self) -> EditPlan:
        if any(op.end > self.source_duration + 0.001 for op in self.operations):
            raise ValueError("An edit extends past the original video. Check its end time.")
        visual = [op for op in self.operations if op.kind in {"zoom", "text", "subtitle"}]
        for i, a in enumerate(visual):
            for b in visual[i + 1 :]:
                overlaps = max(a.start, b.start) < min(a.end, b.end)
                same_zoom = a.kind == b.kind == "zoom"
                same_text = a.kind != "zoom" and b.kind != "zoom" and a.position == b.position
                if overlaps and (same_zoom or same_text):
                    raise ValueError("Overlapping zooms or captions in the same position conflict.")
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
        for op in self.operations:
            if op.kind not in {"zoom", "text", "subtitle"}:
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
        cursor, output = 0.0, 0.0
        spans = []
        for start, end in [*merged, [self.source_duration, self.source_duration]]:
            if start - cursor > 0.001:
                spans.append(KeptSpan(source_start=cursor, source_end=start, output_start=output))
                output += start - cursor
            cursor = max(cursor, end)
        return tuple(spans)

    @property
    def output_duration(self) -> float:
        return round(sum(span.duration for span in self.kept_spans), 6)

    @property
    def has_appearance_choices(self) -> bool:
        return any(op.kind in {"zoom", "text", "subtitle"} for op in self.operations)

    def source_time(self, output_time: float) -> float:
        for span in self.kept_spans:
            if span.output_start <= output_time < span.output_start + span.duration:
                return span.source_start + output_time - span.output_start
        raise ValueError("Output time is outside the edited video.")

    def is_visual_edit(self, output_time: float) -> bool:
        source_time = self.source_time(output_time)
        return any(
            op.kind in {"zoom", "text", "subtitle"} and op.start <= source_time < op.end
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
