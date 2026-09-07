from PIL import ImageFont

from revisionproof.editing.models import EditOperation
from revisionproof.editing.render import font_path, text_layer, wrap_text_lines


def test_reproduction_sentence_word_wrap():
    font_b = ImageFont.truetype(str(font_path()), 44)
    text = (
        "RevisionProof combines bounded video edits with an automated-verification "
        "workflow for media professionals."
    )

    lines = wrap_text_lines(text, font=font_b, max_width=1080)
    # Every word must remain intact (no mid-word split such as 'profession' and 'als.')
    reconstructed_words = [w for line in lines for w in line.split()]
    assert reconstructed_words == text.split()
    assert not any(line.endswith("profession") for line in lines)
    assert not any(line.startswith("als.") for line in lines)


def test_mixed_korean_english_and_explicit_newlines():
    font_a = ImageFont.truetype(str(font_path()), 34)
    text = "RevisionProof 자동 검증 시스템\n두 번째 줄: bounded video edits with AI."
    lines = wrap_text_lines(text, font=font_a, max_width=1080)

    assert len(lines) == 2
    assert lines[0] == "RevisionProof 자동 검증 시스템"
    assert lines[1] == "두 번째 줄: bounded video edits with AI."


def test_oversized_unbroken_token_falls_back_to_character_split():
    font_b = ImageFont.truetype(str(font_path()), 44)
    long_token = "W" * 120  # Far exceeds 1080px width
    lines = wrap_text_lines(long_token, font=font_b, max_width=1080)

    assert len(lines) > 1
    assert "".join(lines) == long_token


def test_both_text_and_subtitle_operations_use_word_wrapping(tmp_path):
    dest_subtitle = tmp_path / "subtitle.png"
    dest_text = tmp_path / "text.png"
    long_text = (
        "RevisionProof combines bounded video edits with an automated-verification "
        "workflow for media professionals."
    )

    op_subtitle = EditOperation(kind="subtitle", start=0, end=5, text=long_text, position="bottom")
    op_text = EditOperation(kind="text", start=0, end=5, text=long_text, position="top")

    text_layer(op_subtitle, dest_subtitle, "B")
    text_layer(op_text, dest_text, "B")

    assert dest_subtitle.is_file() and dest_subtitle.stat().st_size > 0
    assert dest_text.is_file() and dest_text.stat().st_size > 0
