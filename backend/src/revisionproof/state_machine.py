from revisionproof.contracts import RunState, Verdict

ALLOWED_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.INDEXED: {RunState.NOTES_PARSED, RunState.FAILED},
    RunState.NOTES_PARSED: {RunState.EVIDENCE_ANCHORED, RunState.FAILED},
    RunState.EVIDENCE_ANCHORED: {RunState.PREVIEWS_READY, RunState.FAILED},
    RunState.PREVIEWS_READY: {RunState.HUMAN_APPROVED, RunState.FAILED},
    RunState.HUMAN_APPROVED: {RunState.VERSION_UPLOADED, RunState.FAILED},
    RunState.VERSION_UPLOADED: {RunState.VERIFYING, RunState.FAILED},
    RunState.VERIFYING: {RunState.BLOCKED, RunState.READY, RunState.FAILED},
    RunState.BLOCKED: {RunState.VERSION_UPLOADED, RunState.FAILED},
    RunState.READY: set(),
    RunState.FAILED: {
        RunState.INDEXED,
        RunState.NOTES_PARSED,
        RunState.EVIDENCE_ANCHORED,
        RunState.PREVIEWS_READY,
        RunState.HUMAN_APPROVED,
        RunState.VERSION_UPLOADED,
    },
}


def assert_transition(current: RunState, target: RunState) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid state transition: {current} -> {target}")


def release_verdict(verdicts: list[Verdict]) -> tuple[Verdict, bool]:
    if verdicts and all(verdict is Verdict.PASS for verdict in verdicts):
        return Verdict.PASS, True
    if any(verdict is Verdict.ERROR for verdict in verdicts):
        return Verdict.ERROR, False
    if any(verdict is Verdict.NOT_CHECKED for verdict in verdicts):
        return Verdict.NOT_CHECKED, False
    return Verdict.FAIL, False
