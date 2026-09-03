import pytest

from revisionproof.editing.interpret import interpret_local
from revisionproof.editing.models import InterpretEditRequest


@pytest.mark.parametrize(
    "text",
    [
        "2–4초 자막 삭제",
        "Remove the text from 2–4s",
        "2–4초에 자막 제거",
        '2–4초에 "old" 문구를 교체',
        "Replace existing subtitles from 2 to 4 seconds",
    ],
)
def test_caption_removal_never_drafts_a_footage_cut(text):
    result = interpret_local(InterpretEditRequest(text=text, duration=10, start=0, end=10))
    assert result.plan.operations == ()
    assert any("already in the video is not supported" in warning for warning in result.warnings)


def test_explicit_footage_cut_and_literal_caption_still_work():
    result = interpret_local(
        InterpretEditRequest(
            text='Cut 2–4s\n4–8초에 "Remove the text" 자막 표시',
            duration=10,
            start=0,
            end=10,
        )
    )
    assert [op.kind for op in result.plan.operations] == ["cut", "subtitle"]
    assert result.plan.operations[1].text == "Remove the text"
    assert result.warnings == []
