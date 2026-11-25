"""Tokenizer conventions: the dCode-style rule vs apostrophe-preserving rule."""

from __future__ import annotations

from pathlib import Path

from echoquest.tokenizers import tokenize

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_fixture.txt"
TEXT = FIXTURE.read_text("utf-8")


def test_dcode_tokenizer_counts() -> None:
    t = tokenize(TEXT, "dcode")
    # "Echo's" splits into echo + s under this rule.
    assert len(t.tokens) == 94
    assert t.tokens[0].text == "echo"
    assert t.tokens[1].text == "s"


def test_apostrophe_tokenizer_counts() -> None:
    t = tokenize(TEXT, "apostrophe")
    # "Echo's" stays one token: one token fewer overall.
    assert len(t.tokens) == 93
    assert t.tokens[0].text == "echo's"


def test_positions_are_1_based_and_sequential() -> None:
    t = tokenize(TEXT, "dcode")
    assert [tok.index for tok in t.tokens] == list(range(1, len(t.tokens) + 1))


def test_paragraph_and_sentence_units() -> None:
    t = tokenize(TEXT, "dcode")
    assert len(t.paragraphs) == 4  # title + 3 narrative paragraphs
    assert len(t.sentences) == 7


def test_lowercasing_and_punctuation_strip() -> None:
    t = tokenize(TEXT, "dcode")
    words = [tok.text for tok in t.tokens]
    assert "village" in words
    assert "," not in words
    assert all(w == w.lower() for w in words)


def test_unknown_tokenizer_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        tokenize(TEXT, "no-such-rule")


def test_word_position_lookup() -> None:
    from echoquest.tokenizers import find_positions

    t = tokenize(TEXT, "dcode")
    pos = find_positions(["echo", "maze", "fury", "renew"], t.tokens)
    assert pos["echo"] == [1, 32, 47, 69, 83]
    assert pos["maze"] == [52]
    assert pos["fury"] == [53]
    assert pos["renew"] == [55]
