#!/usr/bin/env python3
"""C-vs-Python differential cross-validation of the wallet stack.

Executed stages (2026-11-25 repo audit, Stage 0):

1. Generate N deterministic 12-word vectors: half checksum-valid (entropy
   -> mnemonic), half deliberately checksum-invalid (word-shuffled), plus
   the Trezor vector and two literal natural-order phrases drawn from the
   story-derived candidate sets (checksum-invalid).
2. Derive, with the Python stack (itself locked to the Trezor/BIP39/BIP32
   official vectors by the pytest suite), the BIP39 seed and, for EVERY
   path the C scanner can test, the compressed AND uncompressed hash160.
3. Run the C scanner in ``derive`` mode on the same vectors and compare
   every one of the N x 9 x 2 values.  Hard failures (DERIVE-FAIL /
   PUBKEY-FAIL) and mismatches fail the script loudly — derivation errors
   are never silently counted as negative results.
4. Positive control: compile a copy of the scanner with a synthetic
   TARGET_H160 equal to a known vector's primary-path hash160 and run it
   in ``full`` mode over that vector's own word file.  The match file MUST
   be written (word indices only, never key material) — proving that the
   "0 matches" statements of the real scans come from a code path that is
   demonstrably able to fire.
5. Negative control: the same patched binary over a disjoint word set for
   a bounded budget; asserts no match file appears and records the exact
   covered prefix from the checkpoint state file.

Output: ``results/scan/cross_validation.json`` — counters and hashes only,
no secrets.  Exit status 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from echoquest.bip39 import mnemonic_from_entropy, mnemonic_valid, seed_from_mnemonic  # noqa: E402
from echoquest.utils import public_key_bytes, ripemd160, sha256  # noqa: E402
from echoquest.wallet import derive_priv  # noqa: E402

# every path the C scanner's derive mode prints (keep both sides in sync
# with the `paths`/`names` arrays in scripts/experiments/nochecksum_scan.c)
C_PATHS = [
    "m/44'/0'/0'/0/0",
    "m/0'/0/0",
    "m/0/0",
    "m/0/1",
    "m/0/2",
    "m/0/3",
    "m/0/4",
    "m/1/0",
    "m/1/1",
]

TREZOR_VECTOR = ("abandon abandon abandon abandon abandon abandon abandon "
                 "abandon abandon abandon abandon about").split()

# two literal natural orders of story-derived candidate sets (public research
# data, already documented in docs/HYPOTHESES.md; checksum-invalid)
STORY_PHRASES = [
    "echo more vivid night like maze fury renew hint what they upon".split(),
    "echo next morning armed nothing strong more vivid night maze fury renew".split(),
]


def h160_hex(privkey: int, compressed: bool) -> str:
    pub = public_key_bytes(privkey, compressed)
    return ripemd160(sha256(pub)).hex()


def build_scanner(source: Path, out: Path) -> None:
    cmd = ["gcc", "-O2", "-Wno-deprecated-declarations", "-o", str(out),
           str(source), "-lcrypto"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gcc failed: {proc.stderr[:2000]}")


def patch_target(source_text: str, addr: str, h160: bytes) -> str:
    """Replace TARGET_H160 bytes and TARGET_ADDRESS string in a C source copy."""
    hexes = ", ".join(f"0x{b:02x}" for b in h160)
    new_block = f"static const unsigned char TARGET_H160[20] = {{\n    {hexes}}};"
    text2, n1 = re.subn(
        r"static const unsigned char TARGET_H160\[20\] = \{[^}]*\};",
        new_block, source_text, count=1)
    text3, n2 = re.subn(
        r'static const char \*TARGET_ADDRESS = "[^"]*";',
        f'static const char *TARGET_ADDRESS = "{addr}";', text2, count=1)
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f"patch failed (h160={n1}, addr={n2})")
    return text3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261125)
    ap.add_argument("--source", default="scripts/experiments/nochecksum_scan.c")
    ap.add_argument("--wordlist", default="data/english.txt")
    ap.add_argument("--out", default="results/scan/cross_validation.json")
    ap.add_argument("--positive-budget-s", type=float, default=10.0)
    ap.add_argument("--negative-budget-s", type=float, default=5.0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    repo = Path.cwd()
    src_path = repo / args.source
    wl_path = repo / args.wordlist

    # ---------------- 1. deterministic vectors ----------------
    vectors: list[list[str]] = []
    kinds: list[str] = []

    vectors.append(TREZOR_VECTOR.copy())
    kinds.append("checksum-valid (Trezor vector 0)")
    for words in STORY_PHRASES:
        vectors.append(words.copy())
        kinds.append("story natural order (checksum-invalid)")

    target_n = max(0, args.vectors - len(vectors))
    n_valid = target_n // 2
    n_invalid = target_n - n_valid

    for _ in range(n_valid):
        ent = rng.getrandbits(128).to_bytes(16, "big")
        vectors.append(mnemonic_from_entropy(ent))
        kinds.append("checksum-valid (entropy-derived)")
    for _ in range(n_invalid):
        while True:
            ent = rng.getrandbits(128).to_bytes(16, "big")
            words = mnemonic_from_entropy(ent)
            shuffled = words.copy()
            rng.shuffle(shuffled)
            if shuffled != words and not mnemonic_valid(shuffled):
                break
        vectors.append(shuffled)
        kinds.append("checksum-invalid (shuffled)")

    n = len(vectors)

    # ---------------- 2. Python-side expected values ----------------
    expected: dict[tuple[int, str], tuple[str, str]] = {}
    checksum_flags: dict[int, int] = {}
    for i, words in enumerate(vectors):
        seed = seed_from_mnemonic(words, "")
        checksum_flags[i] = 1 if mnemonic_valid(words) else 0
        for path in C_PATHS:
            k = derive_priv(seed, path)
            expected[(i, path)] = (h160_hex(k, True), h160_hex(k, False))

    # ---------------- 3. run C derive mode and compare ----------------
    with tempfile.TemporaryDirectory(prefix="ncsx-") as td:
        tdp = Path(td)
        binary = tdp / "ncs"
        build_scanner(src_path, binary)
        vecfile = tdp / "vectors.txt"
        vecfile.write_text("\n".join(" ".join(w) for w in vectors) + "\n")
        proc = subprocess.run([str(binary), "derive", str(wl_path), str(vecfile), "-"],
                              capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            print("C derive mode FAILED:", proc.stderr[-2000:], file=sys.stderr)
            return 1
        mismatches: list[str] = []
        rows_checked = 0
        c_checksum_flags: dict[int, int] = {}
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) != 5 or parts[2] in ("DERIVE-FAIL", "PUBKEY-FAIL"):
                mismatches.append(f"hard failure row: {line}")
                continue
            vid, path, hc, hu, csv = parts
            vid_i = int(vid)
            c_checksum_flags[vid_i] = int(csv)
            want = expected[(vid_i, path)]
            rows_checked += 1
            if (hc, hu) != want:
                mismatches.append(f"vector {vid_i} path {path}: C=({hc},{hu}) Py=({want[0]},{want[1]})")
        flag_mismatch = [i for i in checksum_flags
                         if checksum_flags[i] != c_checksum_flags.get(i)]
        if mismatches or flag_mismatch:
            for m in mismatches[:20]:
                print("MISMATCH:", m, file=sys.stderr)
            if flag_mismatch:
                print("checksum-flag mismatches:", flag_mismatch[:10], file=sys.stderr)
            return 1

        # ---------------- 4. positive control ----------------
        v0 = vectors[0]
        v0_seed = seed_from_mnemonic(v0, "")
        k0 = derive_priv(v0_seed, "m/44'/0'/0'/0/0")
        synth_h160 = ripemd160(sha256(public_key_bytes(k0, True)))
        synth_addr = "1" + "A" * 20  # display-only; replaced string is not used for logic
        patched = patch_target(src_path.read_text(), synth_addr, synth_h160)
        patched_path = tdp / "ncs_positive.c"
        patched_path.write_text(patched)
        pos_binary = tdp / "ncs_pos"
        build_scanner(patched_path, pos_binary)
        wordsfile = tdp / "words_pos.txt"
        wordsfile.write_text("\n".join(v0) + "\n")
        pos_prefix = tdp / "pos"
        proc = subprocess.run(
            [str(pos_binary), "full", str(wl_path), str(wordsfile),
             str(pos_prefix), "0", str(args.positive_budget_s)],
            capture_output=True, text=True, timeout=300)
        match_file = pos_prefix.parent / (pos_prefix.name + ".match")
        pos_ok = match_file.is_file()
        pos_detail = {}
        if pos_ok:
            content = match_file.read_text()
            pos_detail = json.loads(content.strip().splitlines()[-1])
            # match records word indices; verify they map back to v0
            from echoquest.bip39 import word_indices
            wl = wl_path.read_text().split()
            want_idx = word_indices(v0, wl)
            pos_ok = pos_detail.get("word_indices") == want_idx and \
                pos_detail.get("path") == "m/44'/0'/0'/0/0" and \
                pos_detail.get("compressed") is True
        if not pos_ok:
            print("POSITIVE CONTROL FAILED — scanner did not (correctly) record the "
                  "synthetic match", file=sys.stderr)
            return 1

        # ---------------- 5. negative control ----------------
        neg_words = vectors[3]  # a different, disjoint checksum-valid vector
        # ensure disjointness from v0 to guarantee no true match is possible
        if set(neg_words) & set(v0):
            for i, w in enumerate(vectors):
                if not (set(w) & set(v0)):
                    neg_words = w
                    break
        wordsfile_neg = tdp / "words_neg.txt"
        wordsfile_neg.write_text("\n".join(neg_words) + "\n")
        neg_prefix = tdp / "neg"
        proc = subprocess.run(
            [str(pos_binary), "full", str(wl_path), str(wordsfile_neg),
             str(neg_prefix), "0", str(args.negative_budget_s)],
            capture_output=True, text=True, timeout=300)
        neg_match = neg_prefix.parent / (neg_prefix.name + ".match")
        neg_ok = not neg_match.exists()
        neg_state = (neg_prefix.name + ".state.b0")
        neg_covered = 0
        neg_state_file = neg_prefix.parent / neg_state
        if neg_state_file.is_file():
            try:
                neg_covered = int(json.loads(neg_state_file.read_text())["offset"])
            except Exception:
                neg_covered = -1
        if not neg_ok:
            print("NEGATIVE CONTROL FAILED — a match fired on a disjoint set",
                  file=sys.stderr)
            return 1

        # ---------------- 6. report ----------------
        out = {
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "vectors": n,
            "vector_kinds": {k: kinds.count(k) for k in sorted(set(kinds))},
            "paths_checked": C_PATHS,
            "rows_checked": rows_checked,
            "expected_rows": n * len(C_PATHS),
            "mismatches": 0,
            "checksum_flag_mismatches": 0,
            "positive_control": {
                "ok": True,
                "vector": "Trezor vector 0 (synthetic target = its own "
                          "m/44'/0'/0'/0/0 compressed hash160)",
                "match_word_indices": pos_detail.get("word_indices"),
                "match_path": pos_detail.get("path"),
                "compressed": pos_detail.get("compressed"),
                "kdf": pos_detail.get("kdf"),
            },
            "negative_control": {
                "ok": True,
                "covered_permutations_in_block0": neg_covered,
                "note": "disjoint word set; no match file written",
            },
            "c_source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
        }
        dest = repo / args.out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        print(json.dumps(out, indent=2, sort_keys=True))
        print(f"cross-validation: {rows_checked}/{out['expected_rows']} rows, "
              f"0 mismatches; positive and negative controls OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
