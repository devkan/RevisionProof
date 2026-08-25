import json
from pathlib import Path

from revisionproof.contracts import SafetyClassification
from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter


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
