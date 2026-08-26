import json
from pathlib import Path

import pytest

from revisionproof.contracts import RevisionNote, SafetyClassification
from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter
from revisionproof.evidence.live import validate_interpretation_grounding


def test_30_golden_feedback_notes_enforce_safety_boundaries() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "feedback_golden.json"
    items = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert len(items) == 30
    interpreter = FixtureInterpreter()
    locator = FixtureEvidenceLocator()
    counts = {classification: 0 for classification in SafetyClassification}
    for item in items:
        note = interpreter.interpret_many(item["text"])[0]
        expected = SafetyClassification(item["classification"])
        assert note.classification is expected
        counts[expected] += 1
        if expected is SafetyClassification.AUTO_PREVIEWABLE:
            parsed = interpreter.interpret(item["text"])
            anchor = locator.locate(parsed)[0]
            assert parsed.patch_type == "PUNCH_IN"
            assert anchor.time_range.start_seconds == 8
            assert anchor.time_range.end_seconds == 14
            assert anchor.source == "fixture.segment_index"
        else:
            assert note.target_phrase is None
    assert counts == {
        SafetyClassification.AUTO_PREVIEWABLE: 12,
        SafetyClassification.NEEDS_CLARIFICATION: 9,
        SafetyClassification.MANUAL_CREATIVE: 9,
    }


def test_live_interpretation_rejects_ungrounded_or_duplicate_notes() -> None:
    feedback = 'When the presenter says "RevisionProof," push in slightly.'
    grounded = RevisionNote(
        note_id="note_01",
        raw_text=feedback,
        intent="Apply a restrained punch-in",
        classification=SafetyClassification.AUTO_PREVIEWABLE,
        confidence=0.91,
        target_phrase="RevisionProof",
        rationale="The feedback names the exact spoken phrase.",
    )
    validate_interpretation_grounding(feedback, [grounded])

    hallucinated = grounded.model_copy(update={"raw_text": "Replace the soundtrack."})
    with pytest.raises(RuntimeError, match="exactly cover"):
        validate_interpretation_grounding(feedback, [hallucinated])

    with pytest.raises(RuntimeError, match="exactly cover"):
        validate_interpretation_grounding(feedback, [grounded, grounded])

    absent_target = grounded.model_copy(update={"target_phrase": "Secret launch code"})
    with pytest.raises(RuntimeError, match="source note"):
        validate_interpretation_grounding(feedback, [absent_target])


def test_live_interpretation_requires_complete_note_coverage_and_per_note_targets() -> None:
    feedback = (
        '1. When the presenter says "RevisionProof," push in slightly.\n'
        "2. Add premium B-roll during the middle section."
    )
    safe = RevisionNote(
        note_id="note_01",
        raw_text='When the presenter says "RevisionProof," push in slightly.',
        intent="Apply a restrained punch-in",
        classification=SafetyClassification.AUTO_PREVIEWABLE,
        confidence=0.91,
        target_phrase="RevisionProof",
        rationale="The feedback names the exact spoken phrase.",
    )
    manual = RevisionNote(
        note_id="note_02",
        raw_text="Add premium B-roll during the middle section.",
        intent="Create branded B-roll",
        classification=SafetyClassification.MANUAL_CREATIVE,
        confidence=0.96,
        rationale="B-roll creation requires a human editor.",
    )
    validate_interpretation_grounding(feedback, [safe, manual])
    inline_feedback = feedback.replace("\n", " ")
    validate_interpretation_grounding(inline_feedback, [safe, manual])

    with pytest.raises(RuntimeError, match="exactly cover"):
        validate_interpretation_grounding(feedback, [safe])

    cross_note_target = manual.model_copy(
        update={
            "classification": SafetyClassification.AUTO_PREVIEWABLE,
            "confidence": 0.9,
            "target_phrase": "RevisionProof",
        }
    )
    with pytest.raises(RuntimeError, match="source note"):
        validate_interpretation_grounding(feedback, [safe, cross_note_target])
