#!/usr/bin/env python3
"""Re-run the corrected phase-18 checks for the paragraph-5 singletons.

Deterministically recomputes:
* the 13-word P5 singleton superset (echo + 12),
* the story-motivated drop-one 12-word variants,
* checksum validity of their natural/reverse orders,
* read-only address comparison of the natural orders (no checksum gate)
  against the puzzle target at a bounded path list.

Uses the local story copy when present; otherwise exits with a message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echoquest import STORY_SHA256, TARGET_ADDRESS  # noqa: E402
from echoquest.bip39 import mnemonic_valid, seed_from_mnemonic  # noqa: E402
from echoquest.sources import load_story  # noqa: E402
from echoquest.tokenizers import tokenize  # noqa: E402
from echoquest.utils import public_key_bytes, ripemd160, sha256  # noqa: E402
from echoquest.wallet import derive_priv  # noqa: E402
from echoquest.wordlists import load_wordlist  # noqa: E402

STORY = REPO / "private" / "story_original.txt"
PATHS = ["m/44'/0'/0'/0/0", "m/0'/0/0", "m/0/0", "m/0'/0", "m/0/0/0", "m"]


def target_h160() -> bytes:
    from echoquest.utils import base58check_decode

    return base58check_decode(TARGET_ADDRESS)[1:]


def main() -> int:
    if not STORY.is_file():
        print("story copy not found (private/); see README")
        return 2
    src = load_story(STORY, STORY_SHA256)
    tt = tokenize(src.text, "dcode")
    wl = load_wordlist()

    p5 = [t for t in tt.tokens if t.paragraph == 5]
    whole = [t.text for t in tt.tokens]
    singletons = [t.text for t in p5 if t.text in wl and whole.count(t.text) == 1]
    superset = ["echo"] + singletons
    print(f"P5 singleton BIP39 words (with echo): {len(superset)}")
    print(" ".join(superset))

    t_h = target_h160()
    results = []
    for drop in ("next", "hint", None):
        words = superset if drop is None else [w for w in superset if w != drop]
        if len(words) != 12:
            continue
        for order_name, ordered in (
            ("natural", words),
            ("reverse", list(reversed(words))),
        ):
            seed = seed_from_mnemonic(ordered)
            row = {
                "variant": f"drop-{drop or 'none'}",
                "order": order_name,
                "checksum_valid": mnemonic_valid(ordered),
                "matches": 0,
                "comparisons": 0,
            }
            for path in PATHS:
                k = derive_priv(seed, path)
                for compressed in (True, False):
                    h = ripemd160(sha256(public_key_bytes(k, compressed)))
                    row["comparisons"] += 1
                    if h == t_h:
                        row["matches"] += 1
            results.append(row)
            print(json.dumps(row))
    out = REPO / "results" / "phase18_corrected.json"
    out.write_text(json.dumps({"target": TARGET_ADDRESS, "results": results}, indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
