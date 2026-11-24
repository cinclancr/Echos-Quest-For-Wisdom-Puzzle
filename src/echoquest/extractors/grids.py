"""Grid-based structural observations (16x32 row-major grid).

The 512-token dCode tokenisation fills a 16x32 grid exactly.  Structural
anchors: ``Echo`` at row 1/col 1 and row 9/col 1; ``Shade`` at row 1/col 14
and row 16/col 14; the dream words at row 9 cols 12-15; the midpoint row
(row 9) is the dream row.  This module re-derives and reports the anchors.
"""

from __future__ import annotations

from ..tokenizers import TokenizedText
from . import ExtractionResult, register

COLUMNS = 32


def grid_words(tokens: TokenizedText, columns: int = COLUMNS) -> list[list[str]]:
    return [[t.text for t in tokens.tokens[r * columns : (r + 1) * columns]] for r in range(len(tokens.tokens) // columns)]


@register("grid-16x32-anchors")
def grid_anchors(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Anchor word positions in the 16x32 grid (informational)."""
    if len(tokens.tokens) != 512:
        return ExtractionResult(
            method="grid-16x32-anchors",
            description="16x32 grid anchor positions",
            words=(),
            positions=(),
            notes=f"requires 512 tokens, got {len(tokens.tokens)}",
        )
    rows = grid_words(tokens)
    report: list[str] = []
    words: list[str] = []
    positions: list[int] = []
    for w in ("echo", "shade", "maze", "fury", "renew", "cryptic"):
        locs = []
        for r, row in enumerate(rows, start=1):
            for c, word in enumerate(row, start=1):
                if word == w:
                    locs.append((r, c))
                    positions.append((r - 1) * COLUMNS + c)
        report.append(f"{w}:{locs}")
        words.extend([w] * len(locs))
    return ExtractionResult(
        method="grid-16x32-anchors",
        description="Anchor positions in the 16x32 row-major grid (informational)",
        words=tuple(words),
        positions=tuple(positions),
        notes="; ".join(report),
    )


@register("row1-vs-row16")
def row1_vs_row16(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Words matching at the same column in rows 1 and 16."""
    if len(tokens.tokens) != 512:
        return ExtractionResult(
            method="row1-vs-row16",
            description="Column-wise matches between rows 1 and 16",
            words=(),
            positions=(),
            notes=f"requires 512 tokens, got {len(tokens.tokens)}",
        )
    rows = grid_words(tokens)
    r1, r16 = rows[0], rows[15]
    matches = [(c, r1[c - 1]) for c in range(1, COLUMNS + 1) if r1[c - 1] == r16[c - 1]]
    return ExtractionResult(
        method="row1-vs-row16",
        description="Column-wise word matches between grid rows 1 and 16",
        words=tuple(w for _, w in matches),
        positions=tuple(c for c, _ in matches),
        notes=f"Matching columns: {[(c, w) for c, w in matches]} — first and last paragraphs parallel each other.",
    )
