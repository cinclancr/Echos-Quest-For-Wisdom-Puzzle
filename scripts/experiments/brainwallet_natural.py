#!/usr/bin/env python3
"""Quick brainwallet-style test for natural-order candidate phrases.

The author's X hint ("I leaked my Bitcoin seed phrase in plain text") invites
testing the most literal historical constructions: the 12 words concatenated
into a string whose SHA-256 *is* the private key (classic brainwallet), for
every natural order of every candidate set.  Read-only; no secrets printed.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nochecksum_natural_orders import SETS  # noqa: E402

from echoquest.utils import ripemd160, sha256  # noqa: E402

TARGET_H160 = ripemd160(sha256(b""))  # placeholder replaced below
from echoquest.utils import base58check_decode  # noqa: E402

TARGET_H160 = base58check_decode("1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx")[1:]


def brainwallet_h160(text: str, compressed: bool) -> bytes:
    from echoquest.utils import public_key_bytes

    k = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big")
    return ripemd160(sha256(public_key_bytes(k, compressed)))


def main() -> int:
    tested = 0
    matches = []
    for label, spec in SETS.items():
        narrative = tuple(spec["narrative"].split())
        orders = {
            "narrative": " ".join(narrative),
            "reverse": " ".join(reversed(narrative)),
            "narrative-nospace": "".join(narrative),
            "reverse-nospace": "".join(reversed(narrative)),
        }
        for name, phrase in orders.items():
            for compressed in (True, False):
                tested += 1
                if brainwallet_h160(phrase, compressed) == TARGET_H160:
                    matches.append({"label": label, "order": name, "compressed": compressed})
                    print("!!! BRAINWALLET MATCH", label, name, compressed)
    print(f"brainwallet comparisons: {tested}, matches: {len(matches)}")
    out = REPO_ROOT / "results" / "scan" / "brainwallet_natural.json"
    out.write_text(
        __import__("json").dumps(
            {
                "experiment": "brainwallet_natural_orders",
                "comparisons": tested,
                "matches": matches,
                "completed_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
