"""Dream-word based rules (Hypothesis E and the 33-bit selectors).

Paragraph 5 (paragraph index 5, the 'next morning' paragraph) contains
twelve BIP39 words that occur exactly once in the whole story:

    next morning armed nothing strong more vivid night maze fury renew hint

Five appear in its first sentence, six in its fourth sentence, and ``hint``
in its fifth sentence.  With ``echo`` prefixed, the first-four-sentences set
yields 11 unknowns (all but ``hint``).
"""

from __future__ import annotations

from ..tokenizers import TokenizedText
from . import ExtractionResult, register


@register("p5-singletons")
def p5_singletons(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """The 12 whole-story singleton BIP39 words of paragraph 5."""
    wl = set(wordlist)
    counts = tokens.counts()
    p5 = [t for t in tokens.tokens if t.paragraph == 5]
    sel = [t for t in p5 if counts[t.text] == 1 and t.text in wl]
    return ExtractionResult(
        method="p5-singletons",
        description="Paragraph-5 BIP39 words occurring exactly once in the story (12 words)",
        words=tuple(t.text for t in sel),
        positions=tuple(t.index for t in sel),
        notes=(
            "Sentence 1: next morning armed nothing strong; sentence 4: more vivid night maze fury renew; "
            "sentence 5: hint. With echo this is 13 words; one word (usually 'next' or 'hint') must be "
            "dropped to form a 12-word mnemonic — the dropping rule is not story-grounded."
        ),
    )


@register("p5-singletons-no-hint")
def p5_singletons_no_hint(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """echo + the 11 P5 singletons excluding 'hint' (first four sentences)."""
    base = p5_singletons(tokens, wordlist)
    words = ["echo"] + [w for w in base.words if w != "hint"]
    positions = [1] + [p for w, p in zip(base.words, base.positions) if w != "hint"]
    return ExtractionResult(
        method="p5-singletons-no-hint",
        description="echo + 11 paragraph-5 singleton BIP39 words excluding 'hint'",
        words=tuple(words),
        positions=tuple(positions),
        notes="Equivalent to the P5 first-four-sentences singletons plus echo.",
    )


@register("p5-singletons-no-next")
def p5_singletons_no_next(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """echo + the 11 P5 singletons excluding 'next'."""
    base = p5_singletons(tokens, wordlist)
    words = ["echo"] + [w for w in base.words if w != "next"]
    positions = [1] + [p for w, p in zip(base.words, base.positions) if w != "next"]
    return ExtractionResult(
        method="p5-singletons-no-next",
        description="echo + 11 paragraph-5 singleton BIP39 words excluding 'next'",
        words=tuple(words),
        positions=tuple(positions),
        notes="'next' read as an instruction (the next words) rather than a seed word.",
    )


@register("dream-words")
def dream_words(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """The three explicitly highlighted dream words."""
    sel = [t for t in tokens.tokens if t.text in ("maze", "fury", "renew")]
    return ExtractionResult(
        method="dream-words",
        description="The explicitly introduced dream words maze, fury, renew",
        words=tuple(t.text for t in sel),
        positions=tuple(t.index for t in sel),
        notes=(
            "BIP39 0-based indices 1100/755/1457 -> 11-bit strings concatenated to 33 bits; "
            "split into eleven 3-bit selectors: 4,2,3,0,5,7,1,6,6,6,1 (first eight are a "
            "permutation of 0..7). Selector interpretation is UNRESOLVED."
        ),
    )


@register("dream-33bits")
def dream_33bits(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """The 33-bit selector code from the dream word indices (informational)."""
    bits = "".join(f"{idx:011b}" for idx in (1100, 755, 1457))
    triples = [int(bits[i : i + 3], 2) for i in range(0, 33, 3)]
    return ExtractionResult(
        method="dream-33bits",
        description="Eleven 3-bit selectors derived from the dream word indices",
        words=tuple(str(x) for x in triples),
        positions=tuple(),
        notes=(
            "maze=10001001100, fury=01011110011, renew=10110110001; concatenated and split into "
            "eleven 3-bit groups: " + ", ".join(map(str, triples)) + ". Post-hoc pattern: treat with caution."
        ),
    )


@register("dream-sentence")
def dream_sentence(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """BIP39 words of the dream sentence (Hypothesis C)."""
    wl = set(wordlist)
    dream = [t for t in tokens.tokens if t.sentence and 246 <= t.index <= 277]
    sel = [t for t in dream if t.text in wl]
    return ExtractionResult(
        method="dream-sentence",
        description="BIP39 words within the dream sentence (Hypothesis C)",
        words=tuple(t.text for t in sel),
        positions=tuple(t.index for t in sel),
        notes="Literal forms only; lemmatised variants (dreams->dream, grew->grow, revealing->reveal) not substituted.",
    )
