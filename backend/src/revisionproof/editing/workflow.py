from __future__ import annotations

import hashlib

from revisionproof.contracts import (
    EditCandidate,
    EvidenceAnchor,
    ParsedFeedback,
    RevisionNote,
    RunState,
    SafetyClassification,
    TimeRange,
)
from revisionproof.editing.models import EditPlan
from revisionproof.editing.render import render_plan, resolve_plan


def review_plan(service, snapshot, plan: EditPlan) -> None:
    with service._exclusive_media_pipeline():
        plan, warnings = resolve_plan(
            plan,
            snapshot.asset.duration_seconds,
            service.repository.source_path(snapshot.run_id),
            service.executor,
        )
    snapshot.edit_plan, snapshot.edit_warnings = plan, warnings
    raw = snapshot.source_feedback or "Review the selected video edits."
    ready = bool(plan.operations)
    snapshot.notes = [
        RevisionNote(
            note_id="edit_plan",
            raw_text=raw,
            intent=f"Review {len(plan.operations)} selected edits.",
            classification=SafetyClassification.AUTO_PREVIEWABLE
            if ready
            else SafetyClassification.MANUAL_CREATIVE,
            confidence=1,
            target_phrase=raw[:200] if ready else None,
            rationale=(
                "Times and text come from your editable plan. Quiet pauses require your selection."
            ),
        )
    ]
    service._transition(snapshot, RunState.NOTES_PARSED, "Your edit plan is ready to review")
    if not ready:
        return
    snapshot.feedback = ParsedFeedback(
        raw_text=raw,
        intent=snapshot.notes[0].intent,
        patch_type="EDIT_PLAN",
        target_phrase=raw[:200],
        rationale=snapshot.notes[0].rationale,
        interpreter_source="user.structured",
    )
    snapshot.evidence = [
        EvidenceAnchor(
            segment_id=f"plan_{snapshot.run_id}",
            time_range=TimeRange(start_seconds=0, end_seconds=plan.source_duration),
            score=1,
            transcript="",
            visual_summary="Original-video times and exact text selected by the user.",
            source="user.selected_range",
        )
    ]
    service._transition(
        snapshot, RunState.EVIDENCE_ANCHORED, "Choose edits and detected cuts before previewing"
    )


def plan_previews(service, snapshot, selection: EditPlan | None) -> None:
    draft = snapshot.edit_plan
    if draft and any(op.detected for op in draft.operations) and selection is None:
        raise ValueError("Select the detected quiet pauses you want to remove before previewing.")
    plan = selection or draft
    if plan is None or not plan.operations or draft is None:
        raise ValueError("Select at least one edit to preview.")
    if plan.source_duration != draft.source_duration or any(
        op not in draft.operations for op in plan.operations
    ):
        raise ValueError(
            "This selection differs from the reviewed draft. Review the edited request again."
        )
    plan.validate_selection()
    candidates = []
    folder = service.settings.runtime_dir / "runs" / snapshot.run_id / "previews"
    source = service.repository.source_path(snapshot.run_id)
    for option in ("A", "B") if plan.has_appearance_choices else ("A",):
        target = folder / f"{option}.mp4"
        render_plan(source, target, plan, option, service.executor)
        with target.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        candidates.append(
            EditCandidate(
                candidate_id=option,
                plan=plan,
                time_range=TimeRange(start_seconds=0, end_seconds=plan.output_duration),
                preview_url=f"/media/runs/{snapshot.run_id}/previews/{option}.mp4",
                reference_sha256=digest,
            )
        )
    snapshot.edit_plan = plan
    snapshot.selected_note_id = "edit_plan"
    snapshot.candidates = candidates
    service._transition(
        snapshot, RunState.PREVIEWS_READY, "Full edited previews are ready for your review"
    )
