import itertools

import pytest

from revisionproof.contracts import RunState, Verdict
from revisionproof.state_machine import assert_transition, release_verdict


def test_happy_and_repair_transitions() -> None:
    path = [
        RunState.INDEXED,
        RunState.NOTES_PARSED,
        RunState.EVIDENCE_ANCHORED,
        RunState.PREVIEWS_READY,
        RunState.HUMAN_APPROVED,
        RunState.VERSION_UPLOADED,
        RunState.VERIFYING,
        RunState.BLOCKED,
        RunState.VERSION_UPLOADED,
        RunState.VERIFYING,
        RunState.READY,
    ]
    for current, target in itertools.pairwise(path):
        assert_transition(current, target)


def test_cannot_skip_human_approval() -> None:
    with pytest.raises(ValueError, match="invalid state transition"):
        assert_transition(RunState.PREVIEWS_READY, RunState.VERIFYING)


@pytest.mark.parametrize(
    ("verdicts", "expected", "allowed"),
    [
        ([Verdict.PASS, Verdict.PASS, Verdict.PASS], Verdict.PASS, True),
        ([Verdict.PASS, Verdict.FAIL, Verdict.PASS], Verdict.FAIL, False),
        ([Verdict.FAIL, Verdict.FAIL, Verdict.PASS], Verdict.FAIL, False),
        ([Verdict.ERROR, Verdict.PASS, Verdict.PASS], Verdict.ERROR, False),
        ([Verdict.NOT_CHECKED, Verdict.PASS, Verdict.PASS], Verdict.NOT_CHECKED, False),
        ([Verdict.FAIL, Verdict.ERROR, Verdict.PASS], Verdict.ERROR, False),
        ([Verdict.FAIL, Verdict.NOT_CHECKED, Verdict.PASS], Verdict.NOT_CHECKED, False),
        ([Verdict.PASS, Verdict.PASS, Verdict.FAIL], Verdict.FAIL, False),
        ([Verdict.PASS, Verdict.FAIL, Verdict.FAIL], Verdict.FAIL, False),
        ([Verdict.ERROR, Verdict.ERROR, Verdict.ERROR], Verdict.ERROR, False),
        ([Verdict.NOT_CHECKED] * 3, Verdict.NOT_CHECKED, False),
        ([], Verdict.FAIL, False),
    ],
)
def test_release_gate_is_fail_closed(
    verdicts: list[Verdict], expected: Verdict, allowed: bool
) -> None:
    assert release_verdict(verdicts) == (expected, allowed)
