from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from revisionproof.contracts import (
    EditCandidate,
    RevisionSpec,
    Verdict,
    VerificationCheck,
    VerificationProof,
)
from revisionproof.editing.sampling import sample_plan_frame
from revisionproof.state_machine import release_verdict
from revisionproof.verification.metrics import audio_levels_db, normalized_similarity, read_frame


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def approved_reference(source: Path, spec: RevisionSpec) -> Path:
    # Recheck the canonical hash at use, including nested values, not just at creation.
    spec = RevisionSpec.model_validate_json(spec.model_dump_json())
    candidate = spec.approved_candidate
    if not isinstance(candidate, EditCandidate):
        raise ValueError("An approved edit-plan reference is required.")
    reference = source.parent.parent / "previews" / f"{candidate.candidate_id}.mp4"
    if not reference.is_file() or file_hash(reference) != candidate.reference_sha256:
        raise ValueError("The approved preview is missing or changed. Start a new review.")
    return reference


def verify_plan(
    source: Path, candidate: Path, spec: RevisionSpec, version_label: str, executor
) -> VerificationProof:
    reference = approved_reference(source, spec)
    edit = spec.approved_candidate
    assert isinstance(edit, EditCandidate)
    plan = edit.plan
    identical = file_hash(candidate) == edit.reference_sha256
    # A file identity requirement protects even a one-frame caption or one changed character.
    # The export is a copy of the user's full approved preview, not another lossy render.
    patch = VerificationCheck(
        check_id="approved_patch",
        label="Export matches your approved preview",
        verdict=Verdict.PASS if identical else Verdict.FAIL,
        failure_code=None if identical else "APPROVED_EXPORT_CHANGED",
        measured={
            "normalized_similarity": int(identical),
            "ratio": int(identical),
            "minimum_winner_margin_observed": int(identical),
            "exact_file_match": int(identical),
        },
        threshold=spec.manifest_for("approved_patch").threshold,
        evidence_time_range=edit.time_range,
    )
    scores = []
    for index in range(max(1, int(plan.output_duration * 2))):
        t = min((index + 0.5) / 2, plan.output_duration - 0.05)
        sample = sample_plan_frame(plan, t)
        actual = read_frame(candidate, t, frame_index=sample.output_frame)
        expected = (
            read_frame(reference, t, frame_index=sample.output_frame)
            if sample.visual_edit
            else read_frame(source, plan.source_time(t), frame_index=sample.source_frame)
        )
        scores.append(normalized_similarity(expected, actual))
    manifest = spec.manifest_for("locked_cta")
    passing = sum(value >= manifest.threshold["minimum_frame_similarity"] for value in scores)
    visual = VerificationCheck(
        check_id="locked_cta",
        label="Kept scenes follow the approved timeline",
        verdict=Verdict.PASS if passing == len(scores) else Verdict.FAIL,
        failure_code=None if passing == len(scores) else "UNEXPECTED_VIDEO_CHANGE",
        measured={
            "ratio": passing / len(scores),
            "passing_frames": passing,
            "sampled_frames": len(scores),
        },
        threshold=manifest.threshold,
        evidence_time_range=manifest.time_range,
    )
    baseline = audio_levels_db(
        reference, start_seconds=0, duration_seconds=plan.output_duration, executor=executor
    )
    revised = audio_levels_db(
        candidate, start_seconds=0, duration_seconds=plan.output_duration, executor=executor
    )
    rms_delta, peak_delta = abs(baseline[0] - revised[0]), abs(baseline[1] - revised[1])
    manifest = spec.manifest_for("locked_audio")
    passed = (
        rms_delta <= manifest.threshold["maximum_rms_delta_db"]
        and peak_delta <= manifest.threshold["maximum_peak_delta_db"] + 1e-9
    )
    audio = VerificationCheck(
        check_id="locked_audio",
        label="Approved audio timeline is preserved",
        verdict=Verdict.PASS if passed else Verdict.FAIL,
        failure_code=None if passed else "LOCKED_AUDIO_CHANGED",
        measured={
            "source_rms_dbfs": round(baseline[0], 2),
            "candidate_rms_dbfs": round(revised[0], 2),
            "source_peak_dbfs": round(baseline[1], 2),
            "candidate_peak_dbfs": round(revised[1], 2),
            "rms_delta_db": round(rms_delta, 2),
            "peak_delta_db": round(peak_delta, 2),
        },
        threshold=manifest.threshold,
        evidence_time_range=manifest.time_range,
    )
    checks = [patch, visual, audio]
    verdict, allowed = release_verdict([c.verdict for c in checks])
    return VerificationProof(
        version_label=version_label,
        spec_hash=spec.spec_hash,
        verdict=verdict,
        publish_allowed=allowed,
        checks=checks,
        generated_at=datetime.now(UTC),
    )
