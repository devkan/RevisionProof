"""Map a single decoded output frame to its approved original frame."""

from dataclasses import dataclass
from math import floor

from revisionproof.editing.models import EditPlan

FPS = 30


@dataclass(frozen=True)
class PlanFrameSample:
    output_frame: int
    source_frame: int
    visual_edit: bool
    requested_edit: bool


def sample_plan_frame(plan: EditPlan, seconds: float) -> PlanFrameSample:
    # Quantize once. Independently seeking source/output milliseconds can round
    # half-frame timestamps in opposite directions after a cut (e.g. 1.25 + .1).
    output_frame = floor(seconds * FPS)
    for span in plan.kept_spans:
        start = round(span.output_start * FPS)
        count = round(span.duration * FPS)
        if start <= output_frame < start + count:
            source_frame = round(span.source_start * FPS) + round(
                (output_frame - start) * span.rate
            )
            visual = any(
                op.kind in {"zoom", "text", "subtitle", "logo"}
                and round(op.start * FPS) <= source_frame < round(op.end * FPS)
                for op in plan.operations
            )
            requested = (
                visual
                or source_frame != output_frame
                or any(
                    op.kind in {"speed", "volume"}
                    and round(op.start * FPS) <= source_frame < round(op.end * FPS)
                    for op in plan.operations
                )
            )
            return PlanFrameSample(output_frame, source_frame, visual, requested)
    raise ValueError("Sample frame is outside the edited video.")
