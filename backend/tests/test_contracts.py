from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from revisionproof.contracts import (
    EvidenceAnchor,
    LockedElement,
    PatchCandidate,
    RevisionNote,
    RevisionSpec,
    SafetyClassification,
    TimeRange,
    VerificationManifest,
)


def make_spec() -> RevisionSpec:
    time_range = TimeRange(start_seconds=8, end_seconds=14)
    return RevisionSpec.freeze(
        run_id="01J00000000000000000000000",
        asset_id="demo_revisionproof_v1",
        candidate=PatchCandidate(candidate_id="B", scale=1.12, time_range=time_range),
        evidence=[
            EvidenceAnchor(
                segment_id="seg_008_014",
                time_range=time_range,
                score=0.97,
                transcript="Reveal",
                visual_summary="Product card",
                source="fixture.segment_index",
            )
        ],
        locked_elements=[
            LockedElement(
                element_id="cta",
                kind="CTA_OVERLAY",
                time_range=TimeRange(start_seconds=24, end_seconds=29),
                description="CTA stays visible",
            ),
            LockedElement(
                element_id="audio",
                kind="AUDIO",
                time_range=TimeRange(start_seconds=0, end_seconds=30),
                description="Audio stays in bounds",
            ),
        ],
        verification_manifest=[
            VerificationManifest(
                check_id="approved_patch",
                time_range=time_range,
                threshold={
                    "minimum_similarity": 0.95,
                    "minimum_winner_margin": 0.0005,
                    "minimum_passing_ratio": 0.8,
                },
            ),
            VerificationManifest(
                check_id="locked_cta",
                time_range=TimeRange(start_seconds=24, end_seconds=29),
                roi=(840, 570, 340, 90),
                threshold={
                    "minimum_frame_similarity": 0.94,
                    "minimum_passing_ratio": 0.6,
                },
            ),
            VerificationManifest(
                check_id="locked_audio",
                time_range=TimeRange(start_seconds=0, end_seconds=30),
                threshold={"maximum_rms_delta_db": 3, "maximum_peak_dbfs": -1},
            ),
        ],
        approved_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    )


def test_spec_hash_is_stable_and_immutable() -> None:
    first = make_spec()
    second = make_spec()
    assert first.spec_hash == second.spec_hash
    assert len(first.spec_hash) == 64
    with pytest.raises(ValidationError):
        first.spec_hash = "tampered"  # type: ignore[misc]


def test_time_range_is_ordered() -> None:
    with pytest.raises(ValidationError):
        TimeRange(start_seconds=14, end_seconds=8)


def test_candidate_scope_rejects_unsupported_scale() -> None:
    with pytest.raises(ValidationError):
        PatchCandidate(
            candidate_id="A", scale=1.2, time_range=TimeRange(start_seconds=8, end_seconds=14)
        )


def test_candidate_scope_rejects_preview_outside_four_to_eight_seconds() -> None:
    with pytest.raises(ValidationError, match="between 4 and 8 seconds"):
        PatchCandidate(
            candidate_id="A", scale=1.05, time_range=TimeRange(start_seconds=8, end_seconds=17)
        )


def test_spec_rejects_a_tampered_canonical_hash() -> None:
    payload = make_spec().model_dump(mode="json")
    payload["approved_candidate"]["scale"] = 1.05
    with pytest.raises(ValidationError, match="hash does not match"):
        RevisionSpec.model_validate(payload)


def test_auto_previewable_note_requires_confident_target() -> None:
    with pytest.raises(ValidationError, match="confidence >= 0.82"):
        RevisionNote(
            note_id="note_01",
            raw_text="Make it better",
            intent="Emphasize something",
            classification=SafetyClassification.AUTO_PREVIEWABLE,
            confidence=0.6,
            rationale="The target is not certain",
        )


@pytest.mark.parametrize("peak_delta", [-0.1, 0.11, float("nan"), float("inf")])
def test_peak_preservation_tolerance_cannot_disable_audio_check(peak_delta) -> None:
    with pytest.raises(ValidationError, match="peak preservation tolerance"):
        VerificationManifest(
            check_id="locked_audio",
            time_range=TimeRange(start_seconds=0, end_seconds=4),
            threshold={"maximum_rms_delta_db": 3, "maximum_peak_delta_db": peak_delta},
        )


def test_legacy_peak_ceiling_still_rejects_positive_values() -> None:
    with pytest.raises(ValidationError, match="at or below 0"):
        VerificationManifest(
            check_id="locked_audio",
            time_range=TimeRange(start_seconds=0, end_seconds=4),
            threshold={"maximum_rms_delta_db": 3, "maximum_peak_dbfs": 1.01},
        )
