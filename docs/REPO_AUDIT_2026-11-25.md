# Independent repository audit — 2026-11-25

Auditor role: independent cryptanalysis researcher and software reviewer.
Repository: <https://github.com/cinclancr/Echos-Quest-For-Wisdom-Puzzle>
Puzzle target (read-only): `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx`
Status at the time of the audit: **UNSOLVED** — no verified mnemonic.

## 1. Remote state at audit start

* HEAD at audit start: `5fa8c2abdf99cd079242c3434aa542b843356264`
  (2026-11-25T00:03:55Z, "Add tests: wordlist anchors, ...").
* Present on `main`: 12 root files (README, LICENSE, pyproject, CHANGELOG,
  CITATION, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, THIRD_PARTY_NOTICES,
  .editorconfig, .gitignore), `.github/ISSUE_TEMPLATE/*` +
  `pull_request_template.md`, `data/` (6 files), `docs/` (14 files),
  `src/echoquest/` (16 files + 8 extractor files), `tests/` (12 files).
* **Missing from `main`:** the whole `scripts/` tree, the whole `results/`
  tree, and `.github/workflows/ci.yml`. Consequences: the README's runnable
  commands 404'd (`scripts/experiments/nochecksum_scan.c` raw URL returned
  HTTP 404), and **no CI had ever executed** because the workflow itself was
  absent. The repository was not reproducible from a clean clone.

## 2. Commands re-run locally (exact outcomes)

| Command | Result at audit start | Result after fixes |
|---|---|---|
| `python -m pip install -e '.[dev]'` | OK (echoquest-1.0.0, ruff-0.17.6) | OK |
| `python -m pytest -q` | 72 passed (4.9 s) | 74 passed |
| `python -m ruff check .` | **26 errors** (13 F401, 4 I001, 2 F841, 2 UP031, 3 UP035, 1 UP033, 1 E713) | **all checks passed** |
| `python scripts/reproduce_baseline.py` | OK — story hash matches pin `437cb7…9a5db0`; wordlist sha `2f5eed…4dbda` | OK |
| `gcc -O2 … nochecksum_scan.c -lcrypto` | OK (2 latent warnings) | clean under `-Wall -Wextra` |
| `nochecksum_scan selftest …` | 5/5 OK (BIP39 Trezor vector, RIPEMD160 KAT, electrum golden, 16/16 goldens, 130/130 EC differential) | unchanged |
| BIP39/BIP32 official vectors | covered by `tests/test_bip39_vectors.py`, `tests/test_bip32_bip44.py`, `tests/test_p2pkh.py` (passing) | unchanged |

## 3. Defects found and fixed

1. **Repository not reproducible** (see §1). Fixed by committing the full
   `scripts/` tree, the small non-secret `results/scan/` fixtures (word
   sets, checkpoint states, goldens, summaries), and the CI workflow. The
   59 MB `results/scan/dset.valid` stays git-ignored, as does everything
   under `private/` (story, any solution).
2. **CI masks failures**: lint had `|| true`, the smoke scan had
   `|| test $? -eq 0` (always green, even on missing files). Fixed: strict
   lint, explicit existence checks on every referenced input, the smoke
   scan must exit 0, and `reproduce_baseline.py` skips only on its
   documented story-absent exit (2).
3. **26 ruff errors** (unused imports, unsorted import blocks, percent
   formatting, unused locals). All fixed; `ruff check .` is clean and part
   of CI.
4. **`docs/HYPOTHESES.md` (hypothesis F) claimed the literal token `shade`
   IS a BIP39 word. False**: the official list contains `shadow` (index
   1574) but not `shade`. Corrected; locked by
   `tests/test_wordlist.py::test_shade_is_not_a_bip39_word_shadow_is` and an
   exact-membership test over the midpoint row (only `after` is a
   non-member).
5. **C-vs-Python differential coverage was thin** (8 golden permutations ×
   2 paths, compressed only). Fixed by a new `derive` mode in the C
   scanner (all 9 derivable paths, compressed + uncompressed hash160) and
   `scripts/experiments/cross_validate.py`:
   **1000 deterministic vectors** (499 checksum-valid / 499 checksum-invalid
   / Trezor vector / 2 story natural orders) × 9 paths × 2 encodings =
   **18,000 hash160 values compared; 0 mismatches**. Hard failures
   (DERIVE-FAIL/PUBKEY-FAIL) exit non-zero — derivation errors are never
   silently counted as negative matches.
6. **Positive control for the "0 matches" claims**: a copy of the scanner
   with a synthetic TARGET_H160 (the Trezor vector's own m/44'/0'/0'/0/0
   compressed hash160) run in `full` mode **did** fire and record the
   expected match (word indices, path, encoding, kdf) — the real scans'
   zero-match results come from a demonstrably working match path.
   Negative control (disjoint word set): no match file, coverage recorded.
7. **Rejection scopes were too broad.** Every REJECTED status in
   `docs/HYPOTHESES.md` now states the exact scope (path, passphrase,
   KDF, encoding) rather than rejecting a word-set wholesale.

## 4. New experiments executed (Stage 2/3)

`scripts/experiments/h1_h5_extraction_audit.py` (deterministic, seed
20261125, 2000 null iterations per model) on the byte-exact pinned story:

* **H1** — 22 preregistered dream-anchored rules: 8 recover the held-out
  trio (`maze`/`fury`/`renew`), **0 produce a complete 12-word set**
  (12-with-echo / 11-without-echo). Best near-miss: the ±15-token window
  around the trio (11 words including echo → only 10 non-echo words).
* **H2** — metatext/marker/narrative-event/boundary-to-centre rule
  batteries: all rejected (no trio recovery, wrong word counts).
* **H3** — window census over all 481 32-token windows: **50 windows have
  ≥ 12 distinct BIP39 words; the midpoint window 257–288 ranks 48th**
  (max observed 14). Four ≥12 windows even start at an `echo` token
  (1, 154, 173, 257). Frequency-preserving token shuffle: P(any window
  ≥12) = 1.0. Joint-alignment null (2nd occurrence of the anchor starts a
  ≥12 window): echo p = 0.1305, frequency-matched alternative anchors
  `of`/`to` p ≈ 0.09 — not significant. The apostrophe-preserving
  tokenizer gives 509 tokens (not 512) and windows of 8–9 words; ±1-token
  shifts of the midpoint row give 11. **The midpoint row's BIP39 density
  is not statistically special; the 512 = 2^9 alignment is
  tokenizer-dependent and is not, by itself, evidence of design.**
* **H4** — paragraph 5's global-singleton BIP39 words are exactly 12
  (`next morning armed nothing strong more vivid night maze fury renew
  hint`); +echo = 13 for 12 slots, so exactly one must be dropped with no
  independent story-grounded rule choosing which. First-4 / final-4
  sentence variants produce 18- and 12-word sets polluted by
  non-singletons.
* **H5** — once-in-each-half BIP39 words number 15; the historical
  11-word "set A" is exactly the ≥4-letter subset of those 15 (the letter
  filter is not story-grounded). Frequency-preserving shuffle null
  p = 0.409; sentence-order-preserving null p = 1.0. **The cross-half
  singleton richness is chance-level.**

## 5. Verification of previous totals against checkpoints

* Electrum-tag scans: 3 sets × 11 blocks, all blocks complete in
  `results/scan/elc_*.state.b*` (33 completed blocks, 0 matches).
* Full no-checksum scan: block 0 at offset 1,028,240 / 3,628,800
  (28.3% of block 0 — cumulative permutations passed; the latest resumed
  session derived 446,464 of them), 0 matches, resumable
  checkpoint committed.
* Natural-order battery: 61,200 comparisons (21 sets × 12 passphrases ×
  15 paths × 2 encodings × 2 KDFs — 61,200 matches the committed
  `nochecksum_natural.json`). Brainwallet: 168 comparisons, 0 matches.
* All counters above are machine-readable in `results/summary.json`.

## 6. Not done / not publishable

* The story text is third-party copyrighted and is **not** committed
  (users supply `private/story_original.txt`; hash-pin verified).
* The 59 MB `results/scan/dset.valid` (checksum-valid enumeration of an
  earlier phase) stays out of Git; its re-verification is documented in
  `docs/RESULTS.md` and reproducible via
  `scripts/experiments/enumerate_valid.py` + `verify_valid.py`.
* GitHub Actions have not yet executed the newly-pushed workflow at the
  time of writing (the workflow was part of the missing files); the first
  push of this audit will trigger the first run.
* No mnemonic, private key, WIF, or recoverable wallet data appears in
  any public file. Puzzle status remains **UNSOLVED**.
