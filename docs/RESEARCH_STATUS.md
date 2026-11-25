# Research status

_Last updated: 2026-11-25 (UTC, independent repo audit)._

**Puzzle status: UNSOLVED.** No mnemonic has been verified against the target
address `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx`. This page tracks what is
VERIFIED, what was tried with exact coverage, and what is next. The full
independent audit (repository reproducibility, factual corrections,
cross-validation and the H1–H5 extraction-rule audit) is in
[REPO_AUDIT_2026-11-25.md](REPO_AUDIT_2026-11-25.md).

## VERIFIED facts

1. **Story provenance** — the byte-exact research copy hashes (SHA-256, UTF-8,
   LF) to `437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0`.
2. **Tokenisation** — dCode-style rule (`[A-Za-z0-9]+`, case-folded,
   apostrophes split, title included): **512 tokens**, 11 paragraphs incl.
   title, 32 narrative sentences. Apostrophe-preserving rule: **509 tokens**.
3. **Anchor positions (1-based, dCode rule)** — `echo`:
   [1, 74, 154, 173, 226, 257, 300, 342, 376, 412, 444]; `grace`: 10
   narrative occurrences; `shade`: [14, 494]; `cryptic`: [249, 274];
   `maze/fury/renew`: 268/269/271.
4. **Midpoint row** — tokens 257–288 start at the second `Echo's` and contain
   **12 distinct BIP39 words** including `echo` and all three dream words
   (`echo more vivid night like maze fury renew hint what they upon`).
   **Audit correction (2026-11-25): this row is NOT statistically special** —
   50 of the 481 possible 32-token windows carry ≥ 12 distinct BIP39 words
   (max 14); this row ranks 48th; ±1-token shifts yield 11; the joint
   anchor-alignment null gives p = 0.1305 (frequency-matched anchors ≈ 0.09).
   The row stays the top word-SET candidate only because of its content
   (all three dream words), not because of its statistics.
5. **Paragraph-5 singletons** — exactly 12 BIP39 words occurring exactly once
   in the story: `next morning armed nothing strong more vivid night maze
   fury renew hint` (+ `echo` = 13; one word must drop for a 12-word phrase
   with no story-grounded rule choosing which — see the H4 audit in
   [EXTRACTION_PRIORITY.md](EXTRACTION_PRIORITY.md)).
6. **Wordlist indices (independently audited)** — `echo=559`, `maze=1100`,
   `fury=755`, `renew=1457`, `armed=94`, `strong=1721` (the last two fix the
   historical mis-entry 97/1727).
7. **Target address structure** — `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx` decodes
   to version `0x00` (P2PKH), hash160 `a6467f506442ff5766bd313515901d9292c84e53`.
8. **Electrum legacy wordlist membership** — `maze`, `fury`, `renew` are NOT
   in the 1626-word legacy list ⇒ the puzzle phrase cannot be an Electrum 1.x
   seed.

## Phase results (2026-11-24/25): the no-checksum turn

Motivated by the maintainer's insight that the twelve words need NOT form a
checksum-valid mnemonic (PBKDF2 works on any words), this phase removed every
checksum gate:

| Experiment | Coverage | Result |
|---|---|---|
| Natural-order battery (21 candidate sets × ~4-6 story orders × 12 passphrases × 2 KDFs × 15 paths × 2 encodings) | 61,200 comparisons | **0 matches** |
| Brainwallet-style (SHA256 of the phrase as private key, 4 string forms × both encodings × 21 sets) | 168 comparisons | **0 matches** |
| Electrum-standard-tag permutation scan, midpoint-32 set (all 11! arrangements; Electrum-version filter, m/0/0) | 39,916,800 perms, ~155K derived | **0 matches** |
| Electrum-standard-tag permutation scan, p5-no-next set | 39,916,800 perms | **0 matches** |
| Electrum-standard-tag permutation scan, p5-no-hint set | 39,916,800 perms | **0 matches** |
| Full no-checksum permutation scan of midpoint-32 set (BIP39 KDF, `m/44'/0'/0'/0/0`, both encodings) | see `results/scan/ncs.state.b*` for the exact, dated checkpoint | in progress |
| Checksum-gated scan (previous phase, same set) | 1,391,882 of 2,492,947 checksum-valid perms at the primary path | 0 matches |

Cross-validation: the C scanner's checksum-valid count over the complete
midpoint set is **2,492,947**, exactly matching the earlier independent Python
enumeration; the scanner's hand-written Montgomery secp256k1 core matches
OpenSSL on 1000+ differential scalars; BIP39/BIP32 outputs match the official
Trezor and BIP-0032 test vectors.

## Tooling cross-validation and extraction-rule audit (2026-11-25)

| Experiment | Coverage | Result |
|---|---|---|
| C-vs-Python differential (`scripts/experiments/cross_validate.py`) | 1000 vectors (499 checksum-valid, 499 checksum-invalid, Trezor vector, 2 story natural orders) × 9 paths × 2 encodings = **18,000 hash160 values** | **0 mismatches** |
| Positive control (synthetic target = Trezor vector's own primary-path hash160) | `full` mode over the vector's own words | match **fired and recorded correctly** — the zero-match scans are meaningful |
| Negative control (disjoint word set) | bounded prefix | no match file written |
| H1–H5 extraction-rule audit (`scripts/experiments/h1_h5_extraction_audit.py`, seed 20261125, 2000-iteration nulls) | 22 H1 rules, 11+ H2 families, full window census, 2 null models | no complete rule; positional/frequency heuristics are chance-level (details in [EXTRACTION_PRIORITY.md](EXTRACTION_PRIORITY.md)) |
| Full no-checksum scan (midpoint-32, block 0) | 446,464 derivations, offset 1,028,240 / 3,628,800 | **0 matches**, resumable |

## Current hypothesis ranking

Maintained with full rationale in
[EXTRACTION_PRIORITY.md](EXTRACTION_PRIORITY.md) (post-audit ranking):

1. **Midpoint-32 row words in an unknown order, BIP39 KDF, primary path,
   checksum-invalid** — the running full scan targets exactly this; the
   audit demoted the *statistical* case for this row to chance-level, so
   the scan outcome now decides it on wallet evidence alone.
2. **Same sets under alternative wallet formats** (custom derivation path,
   passphrase, Electrum with non-zero address index) — partially excluded
   (see table above), partially open.
3. **A different word set entirely** — the extraction rule is still unknown;
   the catalogue in `results/extractions.csv` lists every rule tested, and
   the H1–H5 audit pre-registers the falsification controls for every new
   candidate.

## Open questions

* The author's exact extraction rule (word selection + ordering) — the core
  unsolved problem. The story must define it without external hints.
* The wallet format/derivation used for the address (P2PKH, address index 0
  assumed; BIP44-vs-Electrum-vs-custom unknown).
* Whether the phrase carries a BIP39 passphrase.

## See also

* [REPO_AUDIT_2026-11-25.md](REPO_AUDIT_2026-11-25.md) — the independent
  repository audit (reproducibility, factual fixes, cross-validation).
* [EXTRACTION_PRIORITY.md](EXTRACTION_PRIORITY.md) — pre-registered
  hypotheses, controls, ranking rationale, next decisive experiments.
* [HYPOTHESES.md](HYPOTHESES.md) — the ledger of every extraction rule family.
* [RESULTS.md](RESULTS.md) — raw experiment outcomes with exact coverage.
* [KNOWN_ERRORS.md](KNOWN_ERRORS.md) — historical mistakes and their fixes.
* [HOW_TO_REPRODUCE.md](HOW_TO_REPRODUCE.md) — command-by-command reproduction.
* [SOLUTION.md](SOLUTION.md) — why nothing is claimed as solved.
