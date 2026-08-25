from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from revisionproof.contracts import (
    EvidenceAnchor,
    LockedElement,
    PatchCandidate,
    RevisionSpec,
    TimeRange,
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
            )
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
