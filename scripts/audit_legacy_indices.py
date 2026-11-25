#!/usr/bin/env python3
"""Audit the BIP39 index table against the pinned official wordlist.

Reproduces the historical audit that found ``armed=94`` / ``strong=1721``
(an earlier phase had mis-entered 97 / 1727).  Prints a table of the
research-critical words with their verified 0-based indices, asserts the
pinned wordlist hash, and exits non-zero on any mismatch.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echoquest.wordlists import index_map, load_wordlist  # noqa: E402

PINNED_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"

# (word, VERIFIED 0-based index) — every entry was independently audited.
CRITICAL_WORDS = {
    "echo": 559,
    "maze": 1100,
    "fury": 755,
    "renew": 1457,
    "armed": 94,
    "strong": 1721,
    "next": 1194,
    "morning": 1151,
    "nothing": 1206,
    "vivid": 1961,
    "night": 1196,
    "like": 1037,
    "hint": 862,
    "they": 1796,
    "what": 1998,
    "upon": 1911,
    "more": 1150,
    "shade": 1563,
    "theme": 1849,
    "turn": 1826,
    "shadow": 1561,
    "visit": 1938,
}

# indices that were WRONG in the pre-phase-18 research (kept for the record):
HISTORICAL_ERRORS = {"armed": 97, "strong": 1727}


def main() -> int:
    wl_path = REPO / "data" / "english.txt"
    digest = hashlib.sha256(wl_path.read_bytes()).hexdigest()
    print(f"wordlist sha256: {digest}")
    if digest != PINNED_SHA256:
        print("FAIL: wordlist hash mismatch", file=sys.stderr)
        return 1
    wl = load_wordlist()
    if len(wl) != 2048 or len(set(wl)) != 2048:
        print("FAIL: wordlist size/uniqueness", file=sys.stderr)
        return 1
    im = index_map(wl)
    ok = True
    for w, want in CRITICAL_WORDS.items():
        got = im[w]
        status = "OK" if got == want else "FAIL"
        hist = ""
        if w in HISTORICAL_ERRORS and got != HISTORICAL_ERRORS[w]:
            hist = f"  (historical error was {HISTORICAL_ERRORS[w]})"
        print(f"{status:4s} {w:10s} verified={want:5d} got={got:5d}{hist}")
        ok &= got == want
    print("\naudit result:", "ALL VERIFIED" if ok else "MISMATCHES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
