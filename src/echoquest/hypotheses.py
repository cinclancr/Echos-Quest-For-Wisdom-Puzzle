"""echoquest hypothesis registry: high-level named hypotheses.

The registry documents the hypothesis families from the research history
with their current status, so the CLI and reports can enumerate them.
"""

from __future__ import annotations

from dataclasses import dataclass

STATUS_TAGS = ("VERIFIED", "HYPOTHESIS", "UNTESTED", "REJECTED", "INCOMPLETE")


@dataclass(frozen=True)
class HypothesisInfo:
    """A named hypothesis with its current honest status."""

    hid: str
    family: str
    summary: str
    status: str


HYPOTHESES: tuple[HypothesisInfo, ...] = (
    HypothesisInfo(
        "A",
        "two-halves",
        "Once-in-each-256-token-half BIP39 words with >=4 letters: "
        "upon there wise often wide young remember journey find real ancient",
        "REJECTED",
    ),
    HypothesisInfo(
        "B",
        "frequency",
        "Exactly-two-occurrence four-letter tokens (them->theme prefix completion)",
        "REJECTED",
    ),
    HypothesisInfo(
        "C",
        "dream",
        "Dream-sentence lemmatised words (dream grow more vivid night reveal word like maze fury renew)",
        "REJECTED",
    ),
    HypothesisInfo(
        "D",
        "midpoint",
        "Midpoint row 257-288 distinct BIP39 words: "
        "echo more vivid night like maze fury renew hint what they upon",
        "HYPOTHESIS",
    ),
    HypothesisInfo(
        "E",
        "p5-singletons",
        "Paragraph-5 whole-story singleton BIP39 words: "
        "next morning armed nothing strong more vivid night maze fury renew hint",
        "HYPOTHESIS",
    ),
    HypothesisInfo(
        "F",
        "markers",
        "Echo/Grace parity rule over cross-half repeated words (shade->shadow, turned->turn)",
        "REJECTED",
    ),
    HypothesisInfo(
        "G",
        "markers",
        "Alternate positions of the 22 cross-half words (visions->visit, them->theme, turned->turn)",
        "REJECTED",
    ),
    HypothesisInfo(
        "H",
        "misc",
        "First/last words, noun sets, A1Z26, Vigenere/Beaufort/Autokey, ELS, acrostics",
        "REJECTED",
    ),
    HypothesisInfo(
        "I",
        "triads",
        "33 narrative units as 11 triads with 33-bit dream-word selectors",
        "INCOMPLETE",
    ),
    HypothesisInfo(
        "J",
        "electrum",
        "Electrum native seeds (old 1626-word list; new standard/segwit prefixes)",
        "INCOMPLETE",
    ),
)


def by_id(hid: str) -> HypothesisInfo:
    for h in HYPOTHESES:
        if h.hid == hid:
            return h
    raise KeyError(f"unknown hypothesis {hid!r}")


def all_hypotheses() -> list[HypothesisInfo]:
    return list(HYPOTHESES)
