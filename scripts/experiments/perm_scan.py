#!/usr/bin/env python3
"""Full-permutation address scan for a fixed 12-word candidate set.

Method
------
Word 1 is pinned to ``echo`` (author-stated).  The remaining 11 unknowns are
permuted over positions 2..12 (11! = 39,916,800 arrangements for a set of 11
distinct words; fewer when the multiset has repeats).

Stage A (checksum filter) is cheap: the 128-bit entropy of a 12-word BIP39
mnemonic is the concatenation of the first 11 eleven-bit indices plus the top
7 bits of the 12th word; the 4 checksum bits must equal the top 4 bits of
SHA256(entropy) and are pinned to the low 4 bits of the 12th word's index.
Only ~1/16 of arrangements survive.

Stage B (address scan) derives the BIP39 seed (PBKDF2-HMAC-SHA512, 2048
rounds, empty passphrase) and the BIP32/BIP44 addresses for a bounded set of
paths, comparing each P2PKH hash against the puzzle target.

The scan is checkpointed: progress and any matches are written after every
chunk, so an interrupted run resumes where it stopped.

Read-only: no signing, no transactions, no key material is ever written to
disk.  A match reports the derivation parameters only.
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

from echoquest.utils import SECP256K1_N, hmac_sha512, ripemd160, sha256  # noqa: E402
from echoquest.wordlists import load_wordlist  # noqa: E402

TARGET_HASH160 = bytes.fromhex("a6467f506442ff5766bd313515901d9292c84e53")
TARGET_ADDRESS = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"

DEFAULT_PATHS = [
    "m/44'/0'/0'/0/0",
    "m/0'/0/0",
    "m/0/0",
    "m/0'/0",
    "m/0/0/0",
    "m",
]

EC = None
ENCODING = None
PUBLICFORMAT = None


def _init_ec():
    global EC, ENCODING, PUBLICFORMAT
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    EC = ec
    ENCODING = Encoding
    PUBLICFORMAT = PublicFormat


def compressed_pub(k: int) -> bytes:
    key = EC.derive_private_key(k, EC.SECP256K1())
    return key.public_key().public_bytes(ENCODING.X962, PUBLICFORMAT.CompressedPoint)


def p2pkh_matches(k: int) -> bool:
    """True when P2PKH(compressed, k) equals the target address."""
    return ripemd160(sha256(compressed_pub(k))) == TARGET_HASH160


def ckd(k: int, chain: bytes, index: int) -> tuple[int, bytes]:
    if index >= 0x80000000:
        data = b"\x00" + k.to_bytes(32, "big") + struct.pack(">I", index)
    else:
        data = compressed_pub(k) + struct.pack(">I", index)
    digest = hmac_sha512(chain, data)
    return (int.from_bytes(digest[:32], "big") + k) % SECP256K1_N, digest[32:]


def seed_of(words: tuple[str, ...]) -> bytes:
    return hashlib.pbkdf2_hmac("sha512", " ".join(words).encode("utf-8"), b"mnemonic", 2048, 64)


def derive_keys(seed: bytes, paths: list[list[int]]) -> list[tuple[int, list[int]]]:
    """Return (private key scalar, path) pairs for each parsed path."""
    digest = hmac_sha512(b"Bitcoin seed", seed)
    m_key = int.from_bytes(digest[:32], "big")
    m_chain = digest[32:]
    out = []
    for path in paths:
        k, chain = m_key, m_chain
        ok = True
        for idx in path:
            try:
                k, chain = ckd(k, chain, idx)
            except Exception:
                ok = False
                break
        if ok:
            out.append((k, path))
    return out


def parse_path(path: str) -> list[int]:
    if path == "m":
        return []
    parts = path.strip()[2:].split("/")
    out = []
    for step in parts:
        hardened = step.endswith("'") or step.endswith("h")
        idx = int(step.rstrip("'h"))
        out.append(idx + 0x80000000 if hardened else idx)
    return out


def scan(
    unknowns: tuple[str, ...],
    state_path: Path,
    paths: list[list[int]],
    label: str,
    report_every: int = 200_000,
    first_filter: set[int] | None = None,
    valid_out: Path | None = None,
) -> dict:
    """Scan permutations with checkpointing; returns stats and any match.

    ``first_filter`` restricts the scan to permutations whose first unknown
    word index is in the set (used to split work across workers).  When
    ``valid_out`` is given, every checksum-valid permutation's 12 indices are
    appended as 24 little-endian bytes for later re-testing.
    """
    wl = load_wordlist()
    index_of = {w: i for i, w in enumerate(wl)}
    first_idx = index_of["echo"]
    unknown_idx = [index_of[w] for w in unknowns]
    stats = {
        "label": label,
        "tested": 0,
        "checksum_valid": 0,
        "matches": [],
        "paths": ["m/" + "/".join(str(i - 0x80000000) + "'" if i >= 0x80000000 else str(i) for i in p) if p else "m" for p in paths],
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    t0 = time.perf_counter()
    count = 0
    valid_fh = valid_out.open("ab") if valid_out is not None else None
    try:
        for perm in itertools.permutations(unknown_idx):
            if first_filter is not None and perm[0] not in first_filter:
                continue
            count += 1
            val = first_idx
            for j in range(10):
                val = (val << 11) | perm[j]
            last_word_idx = perm[10]
            val = (val << 7) | (last_word_idx >> 4)
            ent = val.to_bytes(16, "big")
            if (hashlib.sha256(ent).digest()[0] >> 4) == (last_word_idx & 0xF):
                stats["checksum_valid"] += 1
                if valid_fh is not None:
                    valid_fh.write(struct.pack("<12H", first_idx, *perm))
                words = ("echo",) + tuple(wl[i] for i in perm)
                seed = seed_of(words)
                for k, path in derive_keys(seed, paths):
                    if p2pkh_matches(k):
                        match = {
                            "word_indices": [first_idx] + list(perm),
                            "path": "m/" + "/".join(str(i - 0x80000000) + "'" if i >= 0x80000000 else str(i) for i in path) if path else "m",
                            "found_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "note": "indices only; resolve words from the official wordlist",
                        }
                        stats["matches"].append(match)
                        with state_path.with_suffix(".match").open("a", encoding="utf-8") as f:
                            f.write(json.dumps({"label": label, **match}) + "\n")
            if count % report_every == 0:
                elapsed = time.perf_counter() - t0
                with state_path.with_suffix(".progress").open("a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "label": label,
                                "tested": count,
                                "checksum_valid": stats["checksum_valid"],
                                "rate_per_s": round(count / elapsed, 1),
                                "elapsed_s": round(elapsed, 1),
                            }
                        )
                        + "\n"
                    )
    finally:
        if valid_fh is not None:
            valid_fh.close()
    stats["tested"] = count
    stats["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Full-permutation scan (read-only)")
    ap.add_argument("--set", required=True, help="comma-separated 11 unknown words (echo is pinned first)")
    ap.add_argument("--label", default=None)
    ap.add_argument("--paths", default="m/44'/0'/0'/0/0")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "perm_scan.json"))
    ap.add_argument("--report-every", type=int, default=200_000)
    ap.add_argument(
        "--first",
        default=None,
        help="comma-separated 0-based positions among the unknowns; scan only permutations whose first unknown is one of these (worker split)",
    )
    ap.add_argument("--save-valid", default=None, help="binary path to append checksum-valid index tuples (24 bytes each)")
    args = ap.parse_args()

    _init_ec()
    unknowns = tuple(args.set.split(","))
    if len(unknowns) != 11:
        raise SystemExit(f"expected 11 unknown words, got {len(unknowns)}")
    label = args.label or ("set-" + hashlib.sha256(",".join(unknowns).encode()).hexdigest()[:8])
    paths = [parse_path(p) for p in args.paths.split(",")]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    first_filter = None
    if args.first is not None:
        pos = [int(x) for x in args.first.split(",")]
        unknown_idx_ordered = [load_wordlist().index(w) for w in unknowns]
        first_filter = {unknown_idx_ordered[i] for i in pos}
    valid_out = Path(args.save_valid) if args.save_valid else None
    print(f"[{label}] scanning permutations of: {' '.join(unknowns)}", flush=True)
    print(f"paths: {args.paths} first_positions={args.first}", flush=True)
    stats = scan(unknowns, out_path, paths, label, args.report_every, first_filter, valid_out)
    stats["words_redacted"] = True
    out_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(
        f"[{label}] done: tested={stats['tested']} checksum_valid={stats['checksum_valid']} "
        f"matches={len(stats['matches'])}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
