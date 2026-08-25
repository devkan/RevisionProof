import json
from pathlib import Path

from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter


def test_30_golden_feedback_notes_anchor_to_reveal() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "feedback_golden.json"
    items = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert len(items) == 30
    interpreter = FixtureInterpreter()
    locator = FixtureEvidenceLocator()
    for item in items:
        parsed = interpreter.interpret(item["text"])
        anchor = locator.locate(parsed)[0]
        assert parsed.patch_type == "PUNCH_IN"
        assert anchor.time_range.start_seconds == item["start"]
        assert anchor.time_range.end_seconds == item["end"]
        assert anchor.source == "fixture.segment_index"
