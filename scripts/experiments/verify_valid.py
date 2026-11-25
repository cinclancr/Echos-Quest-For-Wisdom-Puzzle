#!/usr/bin/env python3
"""Phase B: verify checksum-valid permutations against the target address.

Reads the binary ``.valid`` file produced by ``enumerate_valid.py`` (records
of 12 uint16 word indices), derives the BIP39 seed (empty passphrase) and
the addresses for a bounded path list, and compares each P2PKH hash against
the puzzle target.  Supports slicing (``--offset``/``--count``) so the work
can be chunked within a bounded wall-clock budget.

A match writes the derivation parameters (and word indices, not words) to
``<out>.match``.  Read-only: no signing, no transactions, no key material.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from perm_scan import _init_ec, derive_keys, p2pkh_matches, parse_path, seed_of  # noqa: E402

from echoquest.wordlists import load_wordlist  # noqa: E402

RECORD = 24  # 12 x uint16


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--valid-file", required=True)
    ap.add_argument("--offset", type=int, default=0, help="record index to start at")
    ap.add_argument("--count", type=int, default=0, help="number of records to process (0 = to end)")
    ap.add_argument("--paths", default="m/44'/0'/0'/0/0")
    ap.add_argument("--uncompressed", action="store_true", help="also test uncompressed P2PKH at the first path")
    ap.add_argument("--time-budget", type=float, default=540.0)
    ap.add_argument("--out", required=True, help="state/match output path (JSON)")
    args = ap.parse_args()

    _init_ec()
    wl = load_wordlist()
    paths = [parse_path(p) for p in args.paths.split(",")]
    valid_path = Path(args.valid_file)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_records = valid_path.stat().st_size // RECORD
    end = total_records if args.count == 0 else min(args.offset + args.count, total_records)
    matches: list[dict] = []
    processed = 0
    t0 = time.perf_counter()
    with valid_path.open("rb") as fh:
        fh.seek(args.offset * RECORD)
        i = args.offset
        while i < end:
            raw = fh.read(RECORD)
            if len(raw) != RECORD:
                break
            if processed % 2048 == 0 and processed > 0 and time.perf_counter() - t0 > args.time_budget:
                break
            indices = struct.unpack("<12H", raw)
            words = tuple(wl[k] for k in indices)
            seed = seed_of(words)
            for k, path in derive_keys(seed, paths):
                if p2pkh_matches(k):
                    matches.append(
                        {
                            "record": i,
                            "indices": list(indices),
                            "path": "m/" + "/".join(str(x - 0x80000000) + "'" if x >= 0x80000000 else str(x) for x in path) if path else "m",
                            "found_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                    )
            processed += 1
            i += 1
    state = {
        "valid_file": str(valid_path),
        "offset": args.offset,
        "next_offset": args.offset + processed,
        "processed": processed,
        "total_records": total_records,
        "paths": args.paths,
        "matches": len(matches),
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "completed": args.offset + processed >= total_records,
    }
    out_path.write_text(json.dumps(state, indent=2) + "\n")
    if matches:
        with out_path.with_suffix(".match").open("a", encoding="utf-8") as f:
            for m in matches:
                f.write(json.dumps(m) + "\n")
    print(json.dumps(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
