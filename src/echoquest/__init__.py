"""echoquest: reproducible research toolkit for the "Echo's Quest For Wisdom" puzzle.

This package implements:

* byte-exact source provenance checks (SHA-256),
* pluggable tokenisers for the story text,
* positional tables (paragraphs, sentences, grids),
* a pinned, verified BIP39 English wordlist,
* spec-conformant BIP39 checksum/seed computation,
* read-only BIP32/BIP44/BIP87-style derivation and P2PKH address encoding,
* a registry of extraction hypotheses ("extractors"),
* a candidate ledger and reporting utilities,
* a command line interface (``python -m echoquest``).

The package never signs transactions, never spends funds and never contacts
the network.  It is a *read-only* analysis toolkit for a publicly announced
puzzle address.
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    "bip39",
    "cli",
    "electrum",
    "hypotheses",
    "ledger",
    "positions",
    "reporting",
    "sources",
    "tokenizers",
    "utils",
    "validators",
    "wallet",
    "wordlists",
]

TARGET_ADDRESS = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"
"""Publicly announced puzzle address (read-only comparison target)."""

STORY_SHA256 = "437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0"
"""SHA-256 of the exact research copy of the story (UTF-8, LF newlines)."""
