"""Acrostic-style extraction rules (dCode conventions).

Reproduces the acrostic families the original solver exported from the dCode
tool, but computed locally from the tokenised text.  The dCode tool convention
(letter/digit runs, apostrophes split, title included) is the ``dcode``
tokenizer.
"""

from __future__ import annotations

from ..tokenizers import TokenizedText
from . import ExtractionResult, register


def _words_by_word_number(tokens: TokenizedText, n: int) -> list[str]:
    """The n-th word of each 'unit' (title + 32 narrative sentences).

    dCode-style acrostic lines are typically sentences; with the title this
gives 33 units.
    """
    units: list[list[str]] = [[t.text for t in tokens.tokens if t.paragraph == 0]]
    for s in range(1, len(tokens.sentences) + 1):
        units.append([t.text for t in tokens.tokens if t.sentence == s])
    out = []
    for unit in units:
        if len(unit) >= n:
            out.append(unit[n - 1])
    return out


@register("acrostic-w1")
def acrostic_w1(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """First word of each unit (title + 32 sentences)."""
    words = _words_by_word_number(tokens, 1)
    return ExtractionResult(
        method="acrostic-w1",
        description="First word of the title and each narrative sentence (33 words)",
        words=tuple(words),
        positions=tuple(),
        notes="Reproduces dCode W1-style acrostic; contains non-BIP39 words; not a candidate mnemonic.",
    )


@register("acrostic-w2")
def acrostic_w2(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Second word of each unit."""
    words = _words_by_word_number(tokens, 2)
    return ExtractionResult(
        method="acrostic-w2",
        description="Second word of the title and each narrative sentence",
        words=tuple(words),
        positions=tuple(),
        notes="Reproduces dCode W2-style acrostic.",
    )


@register("acrostic-w3")
def acrostic_w3(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Third word of each unit."""
    words = _words_by_word_number(tokens, 3)
    return ExtractionResult(
        method="acrostic-w3",
        description="Third word of the title and each narrative sentence",
        words=tuple(words),
        positions=tuple(),
        notes="Reproduces dCode W3-style acrostic.",
    )


@register("acrostic-last")
def acrostic_last(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Last word of each unit."""
    units: list[list[str]] = [[t.text for t in tokens.tokens if t.paragraph == 0]]
    for s in range(1, len(tokens.sentences) + 1):
        units.append([t.text for t in tokens.tokens if t.sentence == s])
    words = [u[-1] for u in units if u]
    return ExtractionResult(
        method="acrostic-last",
        description="Last word of the title and each narrative sentence",
        words=tuple(words),
        positions=tuple(),
        notes="Reproduces dCode W->/L-style acrostic.",
    )


@register("acrostic-paragraph-first")
def acrostic_paragraph_first(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """First word of the title and each paragraph (11 words)."""
    words = []
    for p in tokens.paragraphs:
        p_tokens = [t for t in tokens.tokens if t.paragraph == p.index]
        if p_tokens:
            words.append(p_tokens[0].text)
    return ExtractionResult(
        method="acrostic-paragraph-first",
        description="First word of title + each of the 10 paragraphs",
        words=tuple(words),
        positions=tuple(),
        notes="Title + 10 paragraphs = 11 elements, matching the story's 11-word structure.",
    )


@register("acrostic-paragraph-last")
def acrostic_paragraph_last(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Last word of the title and each paragraph."""
    words = []
    for p in tokens.paragraphs:
        p_tokens = [t for t in tokens.tokens if t.paragraph == p.index]
        if p_tokens:
            words.append(p_tokens[-1].text)
    return ExtractionResult(
        method="acrostic-paragraph-last",
        description="Last word of title + each of the 10 paragraphs",
        words=tuple(words),
        positions=tuple(),
        notes="Title + 10 paragraphs = 11 elements.",
    )
