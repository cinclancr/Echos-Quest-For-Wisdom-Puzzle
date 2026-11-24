"""Extraction hypothesis framework.

Each extractor implements one *story-grounded selection rule* and returns an
:class:`ExtractionResult` with the selected words, their 1-based positions and
an honest provenance note.  Extractors NEVER invent words: every selected word
is a literal token of the input text (prefix-completion rules, where used, are
explicit and flagged).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from ..tokenizers import Token, TokenizedText
from ..wordlists import load_wordlist


@dataclass(frozen=True)
class ExtractionResult:
    """Result of one extraction rule."""

    method: str
    description: str
    words: tuple[str, ...]
    positions: tuple[int, ...]
    notes: str = ""
    prefixes_used: tuple[str, ...] = field(default_factory=tuple)

    @property
    def word_count(self) -> int:
        return len(self.words)

    @property
    def as_row(self) -> dict:
        return {
            "method": self.method,
            "description": self.description,
            "word_count": self.word_count,
            "words": " ".join(self.words),
            "positions": " ".join(map(str, self.positions)),
            "prefixes_used": " ".join(self.prefixes_used) if self.prefixes_used else "",
            "notes": self.notes,
        }


Extractor = Callable[[TokenizedText, list[str]], ExtractionResult]

_REGISTRY: dict[str, Extractor] = {}


def register(name: str) -> Callable[[Extractor], Extractor]:
    """Register an extractor under a stable CLI name."""

    def wrap(fn: Extractor) -> Extractor:
        _REGISTRY[name] = fn
        fn.method_name = name  # type: ignore[attr-defined]
        return fn

    return wrap


def list_methods() -> list[str]:
    return sorted(_REGISTRY)


def run(method: str, tokens: TokenizedText, wordlist: list[str] | None = None) -> ExtractionResult:
    """Run a registered extractor by name."""
    if method not in _REGISTRY:
        raise KeyError(f"unknown method {method!r}; available: {list_methods()}")
    wl = wordlist if wordlist is not None else load_wordlist()
    return _REGISTRY[method](tokens, wl)


def _bip39_filter(tokens: Iterable[Token], wordlist: list[str]) -> list[Token]:
    wl = set(wordlist)
    return [t for t in tokens if t.text in wl]


def _singleton_filter(tokens: Iterable[Token], all_tokens: TokenizedText) -> list[Token]:
    counts = all_tokens.counts()
    return [t for t in tokens if counts[t.text] == 1]


from . import acrostics, book_ciphers, dream, frequency, grids, markers, midpoint  # noqa: E402,F401


def available() -> dict[str, str]:
    """Map method name to its description."""
    out = {}
    for name in _REGISTRY:
        fn = _REGISTRY[name]
        desc = getattr(fn, "__doc__", "") or ""
        out[name] = desc.strip().splitlines()[0] if desc.strip() else name
    return out
