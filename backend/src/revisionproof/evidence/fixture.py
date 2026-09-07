import re

from revisionproof.contracts import (
    EvidenceAnchor,
    ParsedFeedback,
    RevisionNote,
    SafetyClassification,
    TimeRange,
)


class FixtureInterpreter:
    source = "fixture.interpreter"

    def interpret_many(self, raw_text: str) -> list[RevisionNote]:
        raw_notes = [
            re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]
        if not raw_notes:
            raw_notes = [raw_text.strip()]
        return [self._classify(text, index) for index, text in enumerate(raw_notes, start=1)]

    def _classify(self, text: str, index: int) -> RevisionNote:
        normalized = text.casefold()
        manual_markers = ("b-roll", "b roll", "on-brand", "on brand", "new footage")
        clarification_markers = (
            "middle",
            "dynamic",
            "cinematic",
            "feel premium",
            "more premium",
            "less generic",
        )
        if any(marker in normalized for marker in manual_markers):
            classification = SafetyClassification.MANUAL_CREATIVE
            intent = "Add new creative footage with a premium brand treatment."
            confidence = 0.96
            rationale = "B-roll creation is outside the constrained punch-in operation."
            question = None
            target_phrase = None
        elif any(marker in normalized for marker in clarification_markers):
            classification = SafetyClassification.NEEDS_CLARIFICATION
            intent = "Increase energy, but the target moment or permitted change is ambiguous."
            confidence = 0.68
            rationale = "The request needs a precise scene and edit operation before automation."
            question = "Which exact moment should change, and is a center punch-in acceptable?"
            target_phrase = None
        else:
            classification = SafetyClassification.AUTO_PREVIEWABLE
            intent = "Emphasize the product reveal without changing the edit structure."
            confidence = 0.97
            rationale = "A short center punch-in preserves timing, audio, and continuity."
            question = None
            target_phrase = "RevisionProof" if "revisionproof" in normalized else "product reveal"
        return RevisionNote(
            note_id=f"note_{index:02d}",
            raw_text=text,
            intent=intent,
            classification=classification,
            confidence=confidence,
            target_phrase=target_phrase,
            rationale=rationale,
            clarification_question=question,
        )

    def interpret(self, raw_text: str) -> ParsedFeedback:
        note = next(
            (
                item
                for item in self.interpret_many(raw_text)
                if item.classification is SafetyClassification.AUTO_PREVIEWABLE
            ),
            None,
        )
        if note is None or note.target_phrase is None:
            raise ValueError("feedback has no AUTO_PREVIEWABLE note")
        return ParsedFeedback(
            raw_text=note.raw_text,
            intent=note.intent,
            target_phrase=note.target_phrase,
            rationale=note.rationale,
            interpreter_source="fixture.interpreter",
        )


class FixtureEvidenceLocator:
    source = "fixture.segment_index"

    def locate(self, _feedback: ParsedFeedback) -> list[EvidenceAnchor]:
        candidates = [
            EvidenceAnchor(
                segment_id="seg_008_014",
                time_range=TimeRange(start_seconds=8, end_seconds=14),
                score=0.97,
                transcript="Now the whole revision becomes visible in one proof.",
                visual_summary="The central product card resolves into the RevisionProof mark.",
                source="fixture.segment_index",
            ),
            EvidenceAnchor(
                segment_id="seg_014_020",
                time_range=TimeRange(start_seconds=14, end_seconds=20),
                score=0.73,
                transcript="Every approval stays attached to the exact frame range.",
                visual_summary="Evidence rails expand around the main composition.",
                source="fixture.segment_index",
            ),
            EvidenceAnchor(
                segment_id="seg_002_008",
                time_range=TimeRange(start_seconds=2, end_seconds=8),
                score=0.61,
                transcript="Feedback arrives vague. The edit cannot be.",
                visual_summary="An incoming feedback card enters the scene.",
                source="fixture.segment_index",
            ),
        ]
        return candidates
