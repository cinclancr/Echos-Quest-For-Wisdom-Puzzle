"""Frequency-based selection rules.

Hypotheses A and B of the research history: words occurring once in EACH
256-token half, and words occurring exactly twice with exactly four letters.
"""

from __future__ import annotations

from collections import Counter

from ..tokenizers import TokenizedText
from . import ExtractionResult, register


def _halves(tokens: TokenizedText):
    n = len(tokens.tokens)
    assert n % 2 == 0, "half split requires an even token count"
    mid = n // 2
    return tokens.tokens[:mid], tokens.tokens[mid:]


@register("once-in-each-half")
def once_in_each_half(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Word types occurring exactly once in EACH 256-token half (Hypothesis A).

    All such types (22 for the supplied story), then the BIP39 subset (15),
    then the >=4-letter filter (11).  The result reports all three levels so
    no silent filtering occurs.
    """
    a, b = _halves(tokens)
    ca, cb = Counter(t.text for t in a), Counter(t.text for t in b)
    cross = sorted(set(ca) & set(cb) & {w for w, c in ca.items() if c == 1} & {w for w, c in cb.items() if c == 1})
    wl = set(wordlist)
    bip = [w for w in cross if w in wl]
    ge4 = [w for w in bip if len(w) >= 4]
    positions = []
    for t in tokens.tokens:
        if t.text in ge4:
            positions.append(t.index)
    notes = (
        f"22 cross-half singleton types; {len(bip)} are BIP39; {len(ge4)} survive the >=4-letter filter. "
        "The 4-letter filter is NOT story-grounded; 3-letter BIP39 words (cry, day, old...) are excluded "
        "by that filter only."
    )
    return ExtractionResult(
        method="once-in-each-half",
        description="Word types appearing exactly once in each 256-token half, BIP39, >=4 letters (Hypothesis A)",
        words=tuple(ge4),
        positions=tuple(positions),
        notes=notes,
    )


@register("twice-and-four-letters")
def twice_and_four_letters(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Tokens occurring exactly twice in the story with exactly four letters (Hypothesis B).

    Under the dCode tokenisation there are exactly 11 such story tokens; the
    word ``them`` is a BIP39 word's unique four-letter prefix (``theme``).
    Prefix completions are explicitly flagged, never silently substituted.
    """
    counts = tokens.counts()
    wl = set(wordlist)
    selected = [t for t in tokens.tokens if counts[t.text] == 2 and len(t.text) == 4]
    words = [t.text for t in selected]
    positions = [t.index for t in selected]
    prefixes = tuple(w for w in words if w not in wl and any(x.startswith(w) and len(w) >= 4 for x in wordlist))
    return ExtractionResult(
        method="twice-and-four-letters",
        description="Exactly-two-occurrence, exactly-four-letter story tokens (Hypothesis B)",
        words=tuple(words),
        positions=tuple(positions),
        notes=(
            "11 tokens by construction; 'them' is not a BIP39 word but the unique 4-letter "
            "prefix of 'theme'. The interpretation is unsupported by any explicit story clue."
        ),
        prefixes_used=prefixes,
    )


@register("bip39-words-only")
def bip39_words_only(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Every BIP39 word in the story in appearance order (reference set)."""
    wl = set(wordlist)
    sel = [t for t in tokens.tokens if t.text in wl]
    return ExtractionResult(
        method="bip39-words-only",
        description="All BIP39-member story tokens in appearance order",
        words=tuple(t.text for t in sel),
        positions=tuple(t.index for t in sel),
        notes=f"{len(sel)} BIP39 tokens (with repeats) — the superset every positional rule filters.",
    )
