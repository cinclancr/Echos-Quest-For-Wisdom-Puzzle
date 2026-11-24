# Echo's Quest For Wisdom — Bitcoin Steganography Puzzle

**Status: UNSOLVED (ongoing research).** No mnemonic for the puzzle address
has been verified. Nothing in this repository claims otherwise.

This is a reproducible, open-source research project investigating the
publicly announced Bitcoin steganography puzzle **"Echo's Quest For Wisdom"**.
It contains a read-only analysis toolkit, a registry of extraction
hypotheses with per-hypothesis results, the full experimental history of the
investigation, and tooling to continue the search — including a **checksum-agnostic
full-permutation scanner** (C + OpenSSL) that does *not* assume the hidden
twelve words form a checksum-valid BIP39 mnemonic.

| | |
|---|---|
| Puzzle author | IMineBlocks (YouTube channel ID `UCjYHcWGAjUVqU49D2JOKD3w`) |
| Author's video | <https://www.youtube.com/watch?v=k5WIlZcXJHI> |
| Author's X post | <https://x.com/IMineBlocks_com/status/1894292681397829677> |
| Puzzle address (read-only target) | `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx` |
| Announced hint | "The first word is `echo`, the next 11 words can be found within the story text." |
| User-supplied author quote (provenance: user relay, not independently re-verified) | "I leaked my #Bitcoin seed phrase in plain text and after one year the wallet is still safe. How?" |

## What the puzzle is

A short story of ~500 words was published in the video description. Twelve
Bitcoin seed words are hidden in it. The first word is `echo`; the remaining
eleven words are "within the story text". Arranged correctly, they unlock
the wallet for the address above. The story, video and X post belong to their
author; this repository does **not** redistribute them (see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).

## Why "no checksum" matters

Every earlier phase of this investigation (phases 0–18 in the research
history) gated address derivation on BIP39 **checksum validity** — a filter
that keeps only 1/16 of the arrangement space. That is a *validation*
convention, not part of the seed derivation itself: PBKDF2-HMAC-SHA512 over
the mnemonic string works for **any** twelve words. A puzzle author who
hand-picked twelve words from a story can still own a perfectly standard
wallet whose mnemonic fails the checksum (custom tooling, "ignore checksum"
import modes, Electrum-class seed phrases, brainwallet-style tooling, ...).

This repository therefore tests **both** families:

1. **BIP39 (checksum-gated)** — the classic hypothesis space (11! = 39,916,800
   arrangements per candidate word set, ~1/16 checksum-valid).
2. **No-checksum** — the full space, both seed KDFs:
   - BIP39 KDF (salt `mnemonic`) at standard derivation paths, compressed and
     uncompressed P2PKH;
   - Electrum KDF (salt `electrum`) at Electrum standard paths, for
     permutations carrying the Electrum 2.x "new seed" version tag
     (`HMAC-SHA512("Seed version", phrase)` starting with byte `0x01`).

The `scripts/experiments/nochecksum_scan.c` scanner enumerates every
permutation of `echo + 11 unknowns` in exactly the same order as Python
`itertools.permutations`, checkpoints continuously, and records any address
match as word indices only (never raw key material). Its hand-written
Montgomery secp256k1 core is differential-tested against OpenSSL on every
run (see `selftest`).

## Repository layout

```
.
├── src/echoquest/            # installable analysis toolkit (Python)
│   ├── cli.py                # `echoquest` / `python -m echoquest` CLI
│   ├── sources.py            # byte-exact provenance verification
│   ├── tokenizers.py         # pluggable tokenisation rules
│   ├── positions.py          # 1-based positional tables, 16x32 grids
│   ├── wordlists.py          # pinned BIP39 wordlist (hash-checked)
│   ├── bip39.py              # checksum, entropy, seed (PBKDF2)
│   ├── wallet.py             # read-only BIP32/BIP44 derivation, addresses
│   ├── electrum.py           # Electrum new/old seed algorithms
│   ├── extractors/           # registry of extraction hypotheses
│   ├── hypotheses.py         # hypothesis ledger (statuses + evidence)
│   ├── validators.py         # candidate validation
│   ├── ledger.py             # candidate dedup (JSONL/SQLite)
│   ├── reporting.py          # CSV/JSON reporting helpers
│   └── utils.py              # base58, hashes, secp256k1 helpers
├── scripts/
│   ├── experiments/          # heavy scanners (Python + C)
│   │   ├── nochecksum_scan.c     # ★ full-permutation C scanner (no checksum gate)
│   │   ├── nochecksum_natural_orders.py
│   │   ├── brainwallet_natural.py
│   │   ├── enumerate_valid.py    # checksum-valid enumeration (phase A)
│   │   ├── verify_valid.py       # address testing of enumerated perms (phase B)
│   │   └── perm_scan.py          # single-process Python scanner
│   ├── reproduce_baseline.py
│   ├── audit_legacy_indices.py
│   ├── run_phase18.py
│   ├── regenerate_reports.py
│   └── verify_target.py
├── tests/                    # pytest suite (no network, no secrets)
├── docs/                     # research documentation (see index below)
├── data/                     # wordlists (pinned), provenance, fixtures
├── results/                  # generated result tables and scan states
└── private/                  # git-ignored: your local story copy + any solution
```

## Quick start

```bash
# 1. install (editable, with test dependencies)
python -m pip install -e '.[dev]'

# 2. place your legally obtained copy of the story (git-ignored path)
cp /path/to/story.txt private/story_original.txt

# 3. verify provenance and tokenisation
python -m echoquest ingest --input private/story_original.txt --sha256 437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0
python -m echoquest audit  --input private/story_original.txt --tokenizer dcode

# 4. positional table + all extraction hypotheses
python -m echoquest positions --input private/story_original.txt --output results/positions.csv
python -m echoquest extract   --input private/story_original.txt --method all --output results/extractions.csv

# 5. validate a candidate mnemonic file (checksum + indices, redacted)
python -m echoquest test-candidate --candidate-file private/candidates.txt --wordlist data/english.txt

# 6. verify candidates against the puzzle address (read-only)
python -m echoquest verify --candidate-file private/candidates.txt \
       --target 1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx --paths standard \
       --output results/verification-redacted.json

# 7. run the test suite
pytest -q
```

The full no-checksum permutation scanner (requires OpenSSL ≥ 3.0 and a C
compiler):

```bash
gcc -O2 -Wno-deprecated-declarations -o scripts/experiments/nochecksum_scan \
    scripts/experiments/nochecksum_scan.c -lcrypto
# selftest (BIP39 vectors, goldens, fast-EC-vs-OpenSSL differential)
scripts/experiments/nochecksum_scan selftest data/english.txt \
    results/scan/words_dset.txt results/scan/gt all 0 - results/scan/goldens_dset8.tsv
# full scan of the midpoint-32 word set, worker split across 2 cores
scripts/experiments/nochecksum_scan full data/english.txt \
    results/scan/words_dset.txt results/scan/ncs 0,1,2,3,4 0 &
scripts/experiments/nochecksum_scan full data/english.txt \
    results/scan/words_dset.txt results/scan/ncs 5,6,7,8,9,10 0 &
# Electrum-validity filtered scan (~1/256 of permutations survive the tag check)
scripts/experiments/nochecksum_scan electrum1 data/english.txt \
    results/scan/words_dset.txt results/scan/elc_dset 0,1,2,3,4,5,6,7,8,9,10 0
```

Any run appends matches (if any) to `<stateprefix>.match` as word indices
plus derivation parameters — never as raw key material.

## Current research state (2026-11-25)

* The story tokenises to **512 tokens** under the dCode-style rule
  (lowercase `[A-Za-z0-9]+`, apostrophes split, title included) and 509 with
  apostrophe-preserving tokenisation. The midpoint row (tokens 257–288)
  contains twelve distinct BIP39 words including `echo` and all three
  explicit dream words (`maze`, `fury`, `renew`).
* Earlier checksum-gated scanning covered 1,391,882 of the 2,492,947
  checksum-valid permutations of the midpoint set at `m/44'/0'/0'/0/0`
  (no match).
* **This phase removed the checksum gate**: natural orders of every
  catalogued 12-word candidate set were tested across 12 passphrases × 2
  KDFs (BIP39/Electrum) × 15 paths × both encodings — 61,200 comparisons,
  no match. Brainwallet-style constructions of the same orders — 168
  comparisons, no match.
* A full no-checksum permutation scan of the midpoint-32 set and
  Electrum-tag-filtered scans of the top three candidate sets are the
  experiments currently in progress; exact, dated coverage for every run
  is recorded in [docs/RESULTS.md](docs/RESULTS.md) and
  `results/scan/`.

The story itself, its byte-exact hash and the full extraction catalogue
are documented in [docs/](docs/) — start with
[RESEARCH_STATUS.md](docs/RESEARCH_STATUS.md).

## Safety and ethics

* **Read-only.** The toolkit never signs, never broadcasts, never spends.
  It only derives addresses and compares hash160 values.
* If a solution is ever verified, the mnemonic will **not** be published
  here while funds may be live; a redacted proof (word-position hashes,
  derivation parameters) would be published instead, with responsible
  disclosure to the puzzle author. See [SECURITY.md](SECURITY.md).
* Do not use this code with your own personal seed phrase unless you fully
  understand what it computes. It is a research tool, not wallet software.

## Licence

The toolkit code and original documentation are MIT-licensed
([LICENSE](LICENSE), © 2026 cinclancr). The puzzle story, video, transcript,
X post and third-party wordlists are **not** covered by that licence — see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The pinned BIP39 English
wordlist is distributed under its upstream MIT-0-style terms and its SHA-256
is verified at load time.
