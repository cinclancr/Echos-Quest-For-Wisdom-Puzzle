"""Midpoint-row extraction (Hypothesis D).

The 512-token dCode tokenisation splits into two exact 256-token halves; the
second ``Echo's`` sits at position 257, the first token of row 9 of the
16x32 row-major grid.  Filtering tokens 257-288 to exact BIP39 words and
deduplicating (keeping first occurrence) yields exactly 12 distinct words
including ``echo`` — i.e. ``echo`` + 11 unknown words.
"""

from __future__ import annotations

from ..tokenizers import TokenizedText
from . import ExtractionResult, register

ROW_START = 257
ROW_LENGTH = 32


@register("midpoint-32")
def midpoint_32(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Distinct BIP39 words in the 32-token midpoint row (tokens 257-288)."""
    if len(tokens.tokens) != 512:
        return ExtractionResult(
            method="midpoint-32",
            description="Distinct BIP39 words in the 32-token midpoint row",
            words=(),
            positions=(),
            notes=f"requires 512 tokens, got {len(tokens.tokens)}",
        )
    wl = set(wordlist)
    row = list(tokens.tokens[ROW_START - 1 : ROW_START - 1 + ROW_LENGTH])
    assert row[0].text == "echo", "midpoint row must start at the second Echo's"
    seen: set[str] = set()
    words: list[str] = []
    positions: list[int] = []
    for t in row:
        if t.text in wl and t.text not in seen:
            seen.add(t.text)
            words.append(t.text)
            positions.append(t.index)
    note = (
        "Row 9 (tokens 257-288) starts at the second 'Echo's' (the exact 512/2 midpoint) "
        "and contains all three dream words. 12 distinct BIP39 words = echo + 11 candidates. "
        "'like' occurs twice in the row (cols 11 and 27) and is deduplicated."
    )
    return ExtractionResult(
        method="midpoint-32",
        description="Distinct BIP39 words in the 32-token midpoint row 257-288 (Hypothesis D)",
        words=tuple(words),
        positions=tuple(positions),
        notes=note,
    )


@register("midpoint-32-shade-split")
def midpoint_32_shade_split(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """The 6+5 partition of the midpoint row around grid column 14.

    Column 14 holds ``shade`` in rows 1 and 16; in row 9 it holds ``and``.
    BIP39 words left of column 14 (excluding echo): 6 words; right: 5 new
    words (``like`` repeats across both sides).
    """
    if len(tokens.tokens) != 512:
        return ExtractionResult(
            method="midpoint-32-shade-split",
            description="Midpoint row split at the Shade column (col 14)",
            words=(),
            positions=(),
            notes=f"requires 512 tokens, got {len(tokens.tokens)}",
        )
    wl = set(wordlist)
    row = list(tokens.tokens[ROW_START - 1 : ROW_START - 1 + ROW_LENGTH])
    left, right = row[:13], row[13:]
    seen: set[str] = set()
    left_words, right_words = [], []
    left_pos, right_pos = [], []
    for t in left:
        if t.text in wl and t.text != "echo" and t.text not in seen:
            seen.add(t.text)
            left_words.append(t.text)
            left_pos.append(t.index)
    for t in right:
        if t.text in wl and t.text not in seen:
            seen.add(t.text)
            right_words.append(t.text)
            right_pos.append(t.index)
    words = ["echo"] + left_words + right_words
    positions = [ROW_START] + left_pos + right_pos
    return ExtractionResult(
        method="midpoint-32-shade-split",
        description="echo + 6 BIP39 words left of col 14 + 5 right (6+5 split, Hypothesis D variant)",
        words=tuple(words),
        positions=tuple(positions),
        notes=(
            "Column 14 = 'shade' in rows 1/16, 'and' in row 9. 'like' at col 11 (left) is kept; "
            "the col-27 'like' is on the right but already seen. Left+right = 6+5 = 11 unknowns."
        ),
    )
