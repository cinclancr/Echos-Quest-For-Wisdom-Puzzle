"""Pinned official BIP39 English wordlist loading.

The wordlist file ``data/english.txt`` is the byte-exact official list from
the bitcoin/bips repository, mirrored for reproducibility (MIT-licensed
redistribution as done by trezor/python-mnemonic; see
THIRD_PARTY_NOTICES.md).  Its SHA-256 is pinned and enforced.

Known-good index anchors asserted on load:

* ``armed`` -> 94
* ``strong`` -> 1721
* ``echo``  -> 559
* ``maze``  -> 1100
* ``fury``  -> 755
* ``renew`` -> 1457
"""

from __future__ import annotations

import hashlib
from pathlib import Path

WORDLIST_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"
WORDLIST_URL = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
WORDLIST_SIZE = 2048

_ANCHORS = {
    "armed": 94,
    "strong": 1721,
    "echo": 559,
    "maze": 1100,
    "fury": 755,
    "renew": 1457,
}

DEFAULT_WORDLIST_PATH = Path(__file__).resolve().parents[2] / "data" / "english.txt"


class WordlistError(ValueError):
    """Raised when the wordlist fails a pinning check."""


def load_wordlist(path: str | Path | None = None, verify: bool = True) -> list[str]:
    """Load and validate the official BIP39 English wordlist.

    Parameters
    ----------
    path:
        Path to ``english.txt``.  Defaults to the bundled copy.
    verify:
        When True (default) enforce size, uniqueness, alphabetic ordering,
        pinned SHA-256 and index anchors.
    """
    p = Path(path) if path is not None else DEFAULT_WORDLIST_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"BIP39 wordlist not found at {p}; place the official english.txt "
            f"there or download {WORDLIST_URL}"
        )
    raw = p.read_bytes()
    words = raw.decode("ascii").split()
    if verify:
        digest = hashlib.sha256(raw).hexdigest()
        if digest != WORDLIST_SHA256:
            raise WordlistError(
                f"wordlist SHA-256 mismatch: expected {WORDLIST_SHA256}, got {digest}"
            )
        if len(words) != WORDLIST_SIZE or len(set(words)) != WORDLIST_SIZE:
            raise WordlistError("wordlist must contain exactly 2048 unique words")
        if words != sorted(words):
            raise WordlistError("wordlist must be sorted")
        for word, index in _ANCHORS.items():
            if words.index(word) != index:
                raise WordlistError(f"index anchor failed: {word} != {index}")
    return words


def index_map(words: list[str]) -> dict[str, int]:
    """0-based index map for a wordlist."""
    return {w: i for i, w in enumerate(words)}
