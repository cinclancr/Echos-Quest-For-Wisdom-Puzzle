"""Positional tables: rows, grids, windows, anchor words."""

from __future__ import annotations

from pathlib import Path

from echoquest.positions import (
    describe_anchor_words,
    grid_positions,
    position_rows,
    window,
    words_at,
)
from echoquest.tokenizers import tokenize

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_fixture.txt"
T = tokenize(FIXTURE.read_text("utf-8"), "dcode")


def test_position_rows_have_expected_columns() -> None:
    rows = position_rows(T, columns=8)
    assert rows[0].index == 1
    # 94 tokens / 8 columns -> 12 rows
    assert len(rows) == 94
    assert {r.grid16x32_row for r in rows} == set(range(1, 13))


def test_grid_position_of_anchor_words() -> None:
    gp = grid_positions(T, 8, "echo")
    # echo at absolute positions 1, 32, 47, 69, 83 -> (row, col) 1-based
    assert (1, 1) in gp
    assert (4, 8) in gp


def test_words_at_indices() -> None:
    assert words_at(T, [1, 2, 3]) == ["echo", "s", "test"]


def test_window_bounds() -> None:
    w = window(T, 50, 6)
    assert [tok.index for tok in w] == [50, 51, 52, 53, 54, 55]
    assert [tok.text for tok in w][2] == "maze"


def test_anchor_describe() -> None:
    desc = describe_anchor_words(T, ["shade"])
    assert desc["shade"] == [13, 26, 89]
