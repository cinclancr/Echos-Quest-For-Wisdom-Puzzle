#!/usr/bin/env python3
"""Phase A: enumerate checksum-valid permutations of a fixed 11-word set.

Writes every checksum-valid arrangement of ``echo + 11 unknowns`` to a binary
file (12 uint16 little-endian per record = 24 bytes).  Word 1 is pinned to
``echo``.  Supports chunked execution (``--skip``/``--limit``) and a resume
state file so repeated invocations continue where the previous one stopped.

Read-only: no secrets are written; indices are resolvable via the official
BIP39 wordlist.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import struct
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from echoquest.wordlists import load_wordlist  # noqa: E402


def enumerate_valid(unknown_idx: list[int], first_idx: int, out: Path, skip: int, limit: int) -> dict:
    wl = load_wordlist()  # noqa: F841  # wordlist order pinned for reproducibility notes
    t0 = time.perf_counter()
    count = 0
    valid = 0
    with out.open("ab") as fh:
        for perm in itertools.permutations(unknown_idx):
            if count < skip:
                count += 1
                continue
            if limit and count >= skip + limit:
                break
            count += 1
            val = first_idx
            for j in range(10):
                val = (val << 11) | perm[j]
            last = perm[10]
            val = (val << 7) | (last >> 4)
            ent = val.to_bytes(16, "big")
            if (hashlib.sha256(ent).digest()[0] >> 4) == (last & 0xF):
                valid += 1
                fh.write(struct.pack("<12H", first_idx, *perm))
    return {"scanned": count, "valid": valid, "elapsed_s": round(time.perf_counter() - t0, 1)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", required=True, help="comma-separated 11 unknown words")
    ap.add_argument("--out", required=True, help="binary output path (.valid)")
    ap.add_argument("--state", default=None, help="resume state JSON path")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many permutations past --skip (0 = no limit)")
    ap.add_argument("--time-budget", type=float, default=540.0, help="stop after this many seconds")
    args = ap.parse_args()

    wl = load_wordlist()
    unknowns = [w for w in args.set.split(",")]
    if len(unknowns) != 11:
        raise SystemExit("expected 11 unknown words")
    unknown_idx = [wl.index(w) for w in unknowns]
    first_idx = wl.index("echo")

    state_path = Path(args.state) if args.state else Path(args.out).with_suffix(".state")
    skip = 0
    if state_path.exists():
        skip = json.loads(state_path.read_text())["scanned"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    total_expected = 1
    for i in range(2, 12):
        total_expected *= i

    # run with an internal time budget check every 100k permutations
    t0 = time.perf_counter()
    count = skip
    valid = 0
    fh = out.open("ab")
    done = False
    for perm in itertools.permutations(unknown_idx):
        if count < skip:
            count += 1
            continue
        if args.limit and (count - skip) >= args.limit:
            break
        if (count - skip) % 100_000 == 0 and (count - skip) > 0:
            if time.perf_counter() - t0 > args.time_budget:
                break
        val = first_idx
        for j in range(10):
            val = (val << 11) | perm[j]
        last = perm[10]
        val = (val << 7) | (last >> 4)
        ent = val.to_bytes(16, "big")
        if (hashlib.sha256(ent).digest()[0] >> 4) == (last & 0xF):
            valid += 1
            fh.write(struct.pack("<12H", first_idx, *perm))
        count += 1
        if count >= total_expected:
            done = True
            break
    fh.close()
    state = {
        "scanned": count,
        "valid_total": (out.stat().st_size // 24),
        "complete": done or count >= total_expected,
        "total_expected": total_expected,
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
