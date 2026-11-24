"""Name-marker based extraction rules (Echo / Grace / Shade).

The story contains 11 ``Echo``, 10 ``Grace`` and 2 ``Shade`` tokens (title
included, dCode tokenisation).  These extractors test marker-anchored
selection rules: words after each Echo, between marker pairs, and parity
rules over the cross-half repeated words.
"""

from __future__ import annotations

from collections import Counter

from ..tokenizers import TokenizedText
from . import ExtractionResult, register


@register("after-each-echo")
def after_each_echo(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """The token immediately following each of the 11 Echo occurrences."""
    wl = set(wordlist)
    echo_positions = tokens.indices_of("echo")
    words, positions, non_bip = [], [], []
    for p in echo_positions:
        nxt = tokens.token_at(p + 1) if p < len(tokens.tokens) else None
        if nxt is None:
            continue
        if nxt.text in wl:
            words.append(nxt.text)
            positions.append(nxt.index)
        else:
            non_bip.append(nxt.text)
    return ExtractionResult(
        method="after-each-echo",
        description="Token following each of the 11 Echo occurrences",
        words=tuple(words),
        positions=tuple(positions),
        notes=f"Non-BIP39 followers: {' '.join(non_bip)} — rule does not select 11 BIP39 words.",
    )


@register("echo-regions-first-bip39")
def echo_regions_first_bip39(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """First BIP39 word after each Echo marker (bounded by next marker)."""
    wl = set(wordlist)
    echo_positions = tokens.indices_of("echo")
    words, positions, misses = [], [], []
    n = len(tokens.tokens)
    for i, p in enumerate(echo_positions):
        end = echo_positions[i + 1] if i + 1 < len(echo_positions) else n + 1
        found = None
        for q in range(p + 1, min(end, p + 33)):
            t = tokens.token_at(q)
            if t.text in wl:
                found = t
                break
        if found:
            words.append(found.text)
            positions.append(found.index)
        else:
            misses.append(p)
    return ExtractionResult(
        method="echo-regions-first-bip39",
        description="First BIP39 word in each Echo-delimited region",
        words=tuple(words),
        positions=tuple(positions),
        notes=f"{len(words)} found, {len(misses)} regions without a BIP39 word.",
    )


@register("marker-parity")
def marker_parity(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """Cross-half singleton BIP39 words with Echo/Grace parity between occurrences (Hypothesis F).

    Among words occurring exactly once in each 256-token half, keep those
    where the parity of the number of Echo/Grace tokens between the two
    occurrences matches.  Prefix completions required by the historical
    hypothesis (shade->shadow, turned->turn) are flagged, not silently
    substituted.
    """
    counts = tokens.counts()
    wl = set(wordlist)
    n = len(tokens.tokens)
    if n != 512:
        return ExtractionResult(
            method="marker-parity",
            description="Echo/Grace parity rule over cross-half singletons",
            words=(),
            positions=(),
            notes=f"requires 512 tokens, got {n}",
        )
    mid = n // 2
    a, b = tokens.tokens[:mid], tokens.tokens[mid:]
    ca, cb = Counter(t.text for t in a), Counter(t.text for t in b)
    cross = sorted(w for w in ca if ca[w] == 1 and cb.get(w) == 1)
    words, positions = [], []
    for w in cross:
        pos = tokens.indices_of(w)
        if len(pos) != 2:
            continue
        lo, hi = min(pos), max(pos)
        if lo > mid or hi <= mid:
            continue  # not a cross-half pair
        echo_between = sum(1 for p in tokens.indices_of("echo") if lo < p < hi)
        grace_between = sum(1 for p in tokens.indices_of("grace") if lo < p < hi)
        if (echo_between + grace_between) % 2 == 0:
            words.append(w)
            positions.extend(pos)
    prefixes = tuple(w for w in words if w not in wl)
    return ExtractionResult(
        method="marker-parity",
        description="Cross-half singletons with even Echo+Grace count between occurrences (Hypothesis F)",
        words=tuple(words),
        positions=tuple(positions),
        notes=(
            "Historical variant required prefix completions shade->shadow and turned->turn; "
            "flagged rather than substituted."
        ),
        prefixes_used=prefixes,
    )


@register("marker-pairs-alternating")
def marker_pairs_alternating(tokens: TokenizedText, wordlist: list[str]) -> ExtractionResult:
    """One BIP39 word between each consecutive Echo/Grace marker pair (23 markers -> 22 pairs)."""
    wl = set(wordlist)
    markers = [t for t in tokens.tokens if t.text in ("echo", "grace", "shade")]
    words, positions, gaps = [], [], []
    for i in range(len(markers) - 1):
        lo, hi = markers[i].index, markers[i + 1].index
        between = [tokens.token_at(q) for q in range(lo + 1, hi)]
        bip = [t for t in between if t.text in wl]
        if len(between) == 1 and bip:
            words.append(bip[0].text)
            positions.append(bip[0].index)
        else:
            gaps.append(f"{markers[i].text}@{lo}-{markers[i+1].text}@{hi}:{len(between)} tokens")
    return ExtractionResult(
        method="marker-pairs-alternating",
        description="Single BIP39 word isolated between consecutive name markers",
        words=tuple(words),
        positions=tuple(positions),
        notes=f"Failed gaps: {len(gaps)} of {len(markers)-1} pairs; rule does not select 11 words.",
    )
