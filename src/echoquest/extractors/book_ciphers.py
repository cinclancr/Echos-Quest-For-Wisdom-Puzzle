"""Book-cipher style extraction rules.

A book cipher selects words of a codebook by index.  The story (512 tokens)
can serve as its own codebook: e.g. the twelve words at positions given by a
story-derived number sequence.  The rules here are the story-grounded ones
that can be parameterised mechanically.
"""

from __future__ import annotations

from ..tokenizers import TokenizedText
from . import ExtractionResult, register


def _word_at(tokens: TokenizedText, index: int) -> str | None:
    if 1 <= index <= len(tokens.tokens):
        return tokens.token_at(index).text
    return None


@register("cryptic-bracket")
def cryptic_bracket(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """BIP39 words strictly between the two 'cryptic' tokens (positions 249, 274)."""
    positions = tokens.indices_of("cryptic")
    if len(positions) != 2:
        return ExtractionResult(
            method="cryptic-bracket",
            description="Tokens bracketed by the two 'cryptic' occurrences",
            words=(),
            positions=(),
            notes=f"expected 2 'cryptic' tokens, found {len(positions)}",
        )
    lo, hi = positions
    inside = [tokens.token_at(q) for q in range(lo + 1, hi)]
    wl = set(wordlist)
    bip = [t for t in inside if t.text in wl]
    return ExtractionResult(
        method="cryptic-bracket",
        description=f"Tokens between 'cryptic'@{lo} and 'cryptic'@{hi} (24 interior tokens)",
        words=tuple(t.text for t in bip),
        positions=tuple(t.index for t in bip),
        notes=(
            "The bracket contains the second 'Echo's', the dream words and 'cryptic hint' — "
            f"{len(inside)} interior tokens of which {len(bip)} are BIP39."
        ),
    )


@register("a1z26-grace")
def a1z26_grace(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Words at positions derived from GRACE via A1Z26 (G=7,R=18,A=1,C=3,E=5)."""
    letters = [ord(c) - 64 for c in "GRACE"]
    words, positions = [], []
    for v in letters:
        w = _word_at(tokens, v)
        if w:
            words.append(w)
            positions.append(v)
    return ExtractionResult(
        method="a1z26-grace",
        description="Tokens at A1Z26 positions of GRACE (7,18,1,3,5)",
        words=tuple(words),
        positions=tuple(positions),
        notes="Positional code derived from the mentor name; five words only.",
    )


@register("a1z26-shade")
def a1z26_shade(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Words at positions derived from SHADE via A1Z26 (S=19,H=8,A=1,D=4,E=5)."""
    letters = [ord(c) - 64 for c in "SHADE"]
    words, positions = [], []
    for v in letters:
        w = _word_at(tokens, v)
        if w:
            words.append(w)
            positions.append(v)
    return ExtractionResult(
        method="a1z26-shade",
        description="Tokens at A1Z26 positions of SHADE (19,8,1,4,5)",
        words=tuple(words),
        positions=tuple(positions),
        notes="Positional code derived from the village name; five words only.",
    )
