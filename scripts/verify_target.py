#!/usr/bin/env python3
"""Read-only verification of the puzzle target address.

Checks (without any network access):
* Base58Check decode of the announced address,
* version byte (P2PKH) and the hash160 payload,
* round-trip re-encode,
* consistency with the constant used by the scanners.

Optionally verifies one or more candidate mnemonic files against the target
across a bounded path/encoding list (no checksum gate: derivation is valid
for any 12 words).  A match is printed with derivation parameters only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echoquest import TARGET_ADDRESS  # noqa: E402
from echoquest.bip39 import mnemonic_valid, seed_from_mnemonic  # noqa: E402
from echoquest.utils import (  # noqa: E402
    base58check_decode,
    base58check_encode,
    public_key_bytes,
    ripemd160,
    sha256,
)
from echoquest.wallet import derive_priv  # noqa: E402

PATHS = [
    "m/44'/0'/0'/0/0",
    "m/0'/0/0",
    "m/0/0",
    "m/0'/0",
    "m/0/0/0",
    "m/0'/0'",
    "m/0/0/0/0",
    "m/0'/0/0/0",
    "m",
    "m/0/1",
    "m/0/2",
    "m/0/3",
    "m/0/4",
    "m/1/0",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate-file", default=None, help="optional 12-word-per-line candidates")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    raw = base58check_decode(TARGET_ADDRESS)
    info = {
        "address": TARGET_ADDRESS,
        "version_byte": f"{raw[0]:02x}",
        "hash160": raw[1:].hex(),
        "payload_len": len(raw) - 1,
        "roundtrip_ok": base58check_encode(raw) == TARGET_ADDRESS,
        "script_type": "p2pkh (version 0x00)",
    }
    print(json.dumps(info, indent=2))
    if not info["roundtrip_ok"] or info["version_byte"] != "00" or info["payload_len"] != 20:
        print("FAIL: target address failed structural verification", file=sys.stderr)
        return 1

    if args.candidate_file:
        t_h = raw[1:]
        matches = []
        total = 0
        for line in Path(args.candidate_file).read_text().splitlines():
            words = line.split()
            if not words or line.startswith("#"):
                continue
            if len(words) != 12:
                print(f"skip {len(words)}-word line (derivation needs 12)", file=sys.stderr)
                continue
            seed = seed_from_mnemonic(words)
            for path in PATHS:
                k = derive_priv(seed, path)
                for compressed in (True, False):
                    total += 1
                    if ripemd160(sha256(public_key_bytes(k, compressed))) == t_h:
                        matches.append(
                            {
                                "words_redacted": True,
                                "checksum_valid": mnemonic_valid(words),
                                "path": path,
                                "compressed": compressed,
                            }
                        )
        print(f"comparisons: {total}, matches: {len(matches)}")
        if matches:
            print(json.dumps(matches, indent=2))
        if args.json:
            out = Path("results") / "verification-redacted.json"
            out.write_text(
                json.dumps({"target": TARGET_ADDRESS, "matches": matches, "comparisons": total}, indent=2) + "\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
