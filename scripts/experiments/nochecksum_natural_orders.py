#!/usr/bin/env python3
"""No-checksum natural-order address battery.

Rationale
---------
BIP39 seed derivation (PBKDF2-HMAC-SHA512 of the mnemonic string) does NOT
depend on checksum validity: the checksum is a validation convention, not
input to the KDF.  A wallet author who hand-picked twelve words from a story
could have derived a wallet whose BIP39 checksum fails (tools that skip
checksum validation, custom scripts, brainwallet-style tooling, Electrum
imports, etc.).  ALL previous address testing in this project was gated on
checksum validity; this battery removes that gate for the *natural,
story-grounded orders* of every 12-word candidate set ever catalogued.

For each candidate mnemonic we test:

* two seed KDFs: BIP39 (salt ``mnemonic``) and Electrum (salt ``electrum``)
* a bounded path list (BIP44 primary, Electrum defaults, legacy variants)
* compressed AND uncompressed P2PKH encodings
* an optional bounded passphrase list (story-derived)

Only the target address hash160 is compared.  No key material is printed or
written.  A match, if any, is reported with the derivation parameters only.

Run:  python scripts/experiments/nochecksum_natural_orders.py
"""

from __future__ import annotations

import json
import sys
import time
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from echoquest.electrum import mnemonic_to_electrum_seed  # noqa: E402
from echoquest.utils import ripemd160, sha256  # noqa: E402
from echoquest.wallet import derive_priv  # noqa: E402
from echoquest.wordlists import load_wordlist  # noqa: E402

TARGET = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"
# hash160 of the target address (version byte 0x00 stripped)
TARGET_H160 = ripemd160(b"")


def target_hash160(address: str = TARGET) -> bytes:
    from echoquest.utils import base58check_decode

    return base58check_decode(address)[1:]


# --- candidate sets (echo + 11 unknowns) ---------------------------------------

# Each entry: label -> list of word tuples (echo first).  Orders are generated
# separately: narrative-ascending (as listed), descending, alphabetical, and
# set-specific splits.
SETS: dict[str, dict] = {
    # Hypothesis D: distinct BIP39 words of the 32-token midpoint row 257-288.
    "midpoint-32": {
        "narrative": ("echo more vivid night like maze fury renew hint what they upon"),
        "positions": [257, 261, 262, 264, 267, 268, 269, 271, 275, 281, 286, 288],
    },
    # Hypothesis E: paragraph-5 singleton BIP39 words (+ echo = 13; drop-one).
    # The two story-motivated drops:
    "p5-no-hint": {
        "narrative": ("echo next morning armed nothing strong more vivid night maze fury renew"),
        "positions": [1, 214, 215, 216, 218, 224, 261, 262, 264, 268, 269, 271],
    },
    "p5-no-next": {
        "narrative": ("echo morning armed nothing strong more vivid night maze fury renew hint"),
        "positions": [1, 215, 216, 218, 224, 261, 262, 264, 268, 269, 271, 275],
    },
    # Hypothesis A: once-in-each-half words (>=4 letter filter), + echo.
    "once-each-half": {
        "narrative": ("echo upon there wise often wide young remember journey find real ancient"),
        "positions": [1, 7, 15, 18, 36, 42, 71, 153, 157, 179, 193, 239],
    },
    # Hypothesis F: marker-parity set with the historical prefix completions.
    "parity-shadow-turn": {
        "narrative": ("echo upon shadow there wise often wide day remember find cry turn"),
        "positions": [1, 7, 14, 15, 18, 36, 42, 69, 153, 179, 209, 243],
    },
    # Hypothesis F variant: literal 'shade' (NOT a BIP39 word — the official
    # list contains 'shadow', not 'shade'; kept literal because the derivation
    # proceeds without the checksum gate) + turn.
    "parity-shade-turn": {
        "narrative": ("echo upon shade there wise often wide day remember find cry turn"),
        "positions": [1, 7, 14, 15, 18, 36, 42, 69, 153, 179, 209, 243],
    },
    # Hypothesis G: alternate-position set with prefix completions.
    "alt-visit-theme-turn": {
        "narrative": ("echo upon there old wide young visit remember find cry theme turn"),
        "positions": [1, 7, 15, 19, 42, 71, 72, 153, 179, 209, 230, 243],
    },
    # Hypothesis B: twice-and-four-letters with theme completion.
    "twice-four-theme": {
        "narrative": ("echo upon wise wide help will find real into theme like gold"),
        "positions": [1, 7, 18, 42, 87, 175, 179, 193, 230, 238, 267, 391],
    },
    # Literal non-substituted variant of B: keeps 'them' (not a BIP39 word,
    # but the derivation is still well-defined and the author hint says the
    # seed was leaked "in plain text").
    "twice-four-literal-them": {
        "narrative": ("echo upon wise wide help will find real into them like gold"),
        "positions": [1, 7, 18, 42, 87, 175, 179, 193, 230, 286, 391, 441],
    },
    # H4 audit finding (2026-11-25): the FINAL FOUR sentences of paragraph 5
    # (sentences 16-19) yield a formally complete 12-word set with echo and
    # all three dream words.  The rule itself ("final four") is not
    # story-grounded and the set contains non-singleton words (ancient,
    # into, they each occur exactly twice in the story), but it is the only
    # sentence-range rule in the preregistered battery that reaches exactly
    # 12 words — so it is catalogued and battery-tested like the others.
    "p5-final-four": {
        "narrative": ("echo ancient into they more vivid night like maze fury renew hint"),
        "positions": [1, 233, 238, 247, 257, 261, 262, 264, 267, 268, 269, 271, 275],
        "note": "final-four-sentences of paragraph 5; complete 12-word candidate, "
                "non-singleton members flagged; H4 audit 2026-11-25",
    },
}

# Drop-one variants of the 13-word paragraph-5 singleton superset
# (echo + next morning armed nothing strong more vivid night maze fury renew hint).
P5_ALL = "echo next morning armed nothing strong more vivid night maze fury renew hint".split()
for drop in P5_ALL[1:]:
    label = f"p5-drop-{drop}"
    words = [w for w in P5_ALL if w != drop]
    SETS[label] = {
        "narrative": " ".join(words),
        "positions": [1, 214, 215, 216, 218, 224, 261, 262, 264, 268, 269, 271, 275][: len(words)],
        "note": "drop-one variant of the 13-word P5 singleton superset",
    }

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
    # Electrum new-seed standard wallet address indices (m/0/i receiving).
    "m/0/0",
    "m/0/1",
    "m/0/2",
    "m/0/3",
    "m/0/4",
    "m/1/0",
]

PASSPHRASES = [
    "",
    "echo",
    "wisdom",
    "shade",
    "grace",
    "falcon",
    "castle",
    "forest",
    "book",
    "maze",
    "Echo's Quest For Wisdom",
    "Echos Quest For Wisdom",
]


def bip39_seed(words: tuple[str, ...], passphrase: str) -> bytes:
    m = unicodedata.normalize("NFKD", " ".join(words))
    salt = unicodedata.normalize("NFKD", ("mnemonic" + passphrase))
    import hashlib

    return hashlib.pbkdf2_hmac("sha512", m.encode("utf-8"), salt.encode("utf-8"), 2048, 64)


def address_h160(k: int, compressed: bool) -> bytes:
    from echoquest.utils import public_key_bytes

    return ripemd160(sha256(public_key_bytes(k, compressed)))


def main() -> int:
    t_h160 = target_hash160()
    wl = load_wordlist()
    index_of = {w: i for i, w in enumerate(wl)}
    out_lines: list[str] = []
    matches: list[dict] = []
    tested = 0
    t0 = time.perf_counter()

    for label, spec in SETS.items():
        narrative = tuple(spec["narrative"].split())
        orders = {
            "narrative": narrative,
            "reverse": tuple(reversed(narrative)),
            "alphabetical": tuple(sorted(narrative)),
            "alpha-rev": tuple(sorted(narrative, reverse=True)),
        }
        # midpoint set: also the 6+5 shade-column split == narrative order,
        # and the row-interleaved variant (alternate first/second half of row).
        if label == "midpoint-32":
            left = narrative[1:7]
            right = narrative[7:]
            orders["split-6-5"] = ("echo",) + left + right
            orders["split-interleaved"] = ("echo",) + tuple(w for pair in zip(left, right) for w in pair)
        for order_name, words in orders.items():
            if len(words) != 12:
                continue
            non_bip39 = [w for w in words if w not in index_of]
            checksum = None
            if not non_bip39:
                from echoquest.bip39 import mnemonic_valid

                checksum = mnemonic_valid(list(words))
            electrum_std_prefix = None
            # Electrum seed-version classification (informational)
            import hmac as _hmac

            d = _hmac.new(b"Seed version", " ".join(words).encode("utf-8"), "sha512").hexdigest()
            if d.startswith("01"):
                electrum_std_prefix = "standard"
            elif d.startswith("100"):
                electrum_std_prefix = "segwit"
            for passphrase in PASSPHRASES:
                seeds = {
                    "bip39": bip39_seed(words, passphrase),
                    "electrum": mnemonic_to_electrum_seed(" ".join(words), passphrase),
                }
                for seed_name, seed in seeds.items():
                    for path in PATHS:
                        try:
                            k = derive_priv(seed, path)
                        except Exception:
                            continue
                        for compressed in (True, False):
                            tested += 1
                            if address_h160(k, compressed) == t_h160:
                                match = {
                                    "label": label,
                                    "order": order_name,
                                    "passphrase": passphrase,
                                    "kdf": seed_name,
                                    "path": path,
                                    "compressed": compressed,
                                    "words_redacted": True,
                                }
                                matches.append(match)
                                print("!!! MATCH", json.dumps(match), flush=True)
            out_lines.append(
                json.dumps(
                    {
                        "label": label,
                        "order": order_name,
                        "bip39_membership": len([w for w in words if w in index_of]),
                        "checksum_valid": checksum,
                        "electrum_version": electrum_std_prefix,
                        "positions": spec.get("positions"),
                    }
                )
            )
    elapsed = time.perf_counter() - t0
    out = {
        "experiment": "nochecksum_natural_orders",
        "target": TARGET,
        "sets": len(SETS),
        "passphrases": PASSPHRASES,
        "paths": PATHS,
        "comparisons": tested,
        "matches": matches,
        "elapsed_s": round(elapsed, 1),
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "natural orders only, no checksum gate; full permutation scan is separate",
    }
    outpath = REPO_ROOT / "results" / "scan" / "nochecksum_natural.json"
    outpath.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (REPO_ROOT / "results" / "scan" / "nochecksum_natural_detail.jsonl").write_text(
        "\n".join(out_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "passphrases"}, indent=2))
    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
