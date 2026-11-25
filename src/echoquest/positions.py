"""Positional tables: 1-based indices, paragraphs, sentences, grids, CSV export.

All positional claims about the story are re-derived here from the tokenised
text so that every earlier manual observation can be checked mechanically.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .tokenizers import Token, TokenizedText


@dataclass(frozen=True)
class PositionRow:
    """One row of the positions CSV."""

    index: int
    word: str
    paragraph: int
    sentence: int
    char_start: int
    char_end: int
    grid16x32_row: int
    grid16x32_col: int
    in_first_half_256: bool


def position_rows(tokens: TokenizedText, columns: int = 32) -> list[PositionRow]:
    """Build the full positional table for a tokenised text."""
    rows: list[PositionRow] = []
    n = len(tokens.tokens)
    half = n // 2 if n % 2 == 0 else None
    for i, t in enumerate(tokens.tokens):
        row, col = divmod(i, columns)
        rows.append(
            PositionRow(
                index=t.index,
                word=t.text,
                paragraph=t.paragraph,
                sentence=t.sentence,
                char_start=t.char_start,
                char_end=t.char_end,
                grid16x32_row=row + 1,
                grid16x32_col=col + 1,
                in_first_half_256=half is not None and t.index <= half,
            )
        )
    return rows


def write_positions_csv(tokens: TokenizedText, out_path: str | Path, columns: int = 32) -> Path:
    """Write the positions CSV (1-based, both grids)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "index",
                "word",
                "paragraph",
                "sentence",
                "char_start",
                "char_end",
                "grid16x32_row",
                "grid16x32_col",
                "in_first_half_256",
            ]
        )
        for r in position_rows(tokens, columns):
            writer.writerow(
                [
                    r.index,
                    r.word,
                    r.paragraph,
                    r.sentence,
                    r.char_start,
                    r.char_end,
                    r.grid16x32_row,
                    r.grid16x32_col,
                    int(r.in_first_half_256),
                ]
            )
    return out


def words_at(tokens: TokenizedText, indices: Iterable[int]) -> list[str]:
    """Surface forms at the given 1-based token indices."""
    return [tokens.token_at(i).text for i in indices]


def window(tokens: TokenizedText, start: int, length: int) -> list[Token]:
    """The ``length`` tokens starting at 1-based index ``start``."""
    if start < 1 or start + length - 1 > len(tokens.tokens):
        raise ValueError("window out of range")
    return list(tokens.tokens[start - 1 : start - 1 + length])


def describe_anchor_words(tokens: TokenizedText, words: Iterable[str]) -> dict[str, list[int]]:
    """Position lists for anchor words (case-folded exact matches)."""
    return {w: tokens.indices_of(w) for w in words}


def grid_positions(tokens: TokenizedText, columns: int, word: str) -> list[tuple[int, int]]:
    """(row, col) pairs of a word in the row-major grid."""
    out: list[tuple[int, int]] = []
    w = word.lower()
    for i, t in enumerate(tokens.tokens):
        if t.text == w:
            row, col = divmod(i, columns)
            out.append((row + 1, col + 1))
    return out
