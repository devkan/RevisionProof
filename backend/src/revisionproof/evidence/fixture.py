from revisionproof.contracts import EvidenceAnchor, ParsedFeedback, TimeRange


class FixtureInterpreter:
    source = "fixture.interpreter"

    def interpret(self, raw_text: str) -> ParsedFeedback:
        return ParsedFeedback(
            raw_text=raw_text,
            intent="Emphasize the product reveal without changing the edit structure.",
            target_phrase="product reveal",
            rationale=(
                "A short center punch-in adds emphasis while preserving timing and continuity."
            ),
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
