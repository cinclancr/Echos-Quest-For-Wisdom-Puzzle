# Results — experiments actually executed

Every row below was run by the code in this repository (or its audited
predecessor scripts, re-verified here).  Dates are UTC.  "0 matches" means
the target hash160 `a6467f506442ff5766bd313515901d9292c84e53` was not
produced within the stated, exact coverage.

## 2026-11-24 — natural-order no-checksum battery

* Script: `scripts/experiments/nochecksum_natural_orders.py`
* Output: `results/scan/nochecksum_natural.json` +
  `nochecksum_natural_detail.jsonl`
* Coverage: 21 candidate sets × orders (narrative/reverse/alphabetical/
  alpha-rev + set-specific splits) × 12 passphrases × KDFs {BIP39, Electrum}
  × 15 paths × {compressed, uncompressed} = **61,200 address comparisons**.
* Result: **0 matches**. No candidate's natural order reproduces the target
  under either seed KDF, any of the tested paths/passphrases or encodings.
* Notes: this removed the checksum gate for every natural order; earlier
  phases only ever derived checksum-valid phrases.

## 2026-11-24 — brainwallet-style tests

* Script: `scripts/experiments/brainwallet_natural.py`
* Output: `results/scan/brainwallet_natural.json`
* Coverage: 21 sets × 4 phrase forms × 2 encodings = **168 comparisons**
  (privkey = SHA256(phrase-string)).
* Result: **0 matches**.

## 2026-11-24/25 — Electrum-standard-tag permutation scans

* Binary: `scripts/experiments/nochecksum_scan.c` (mode `electrum1`)
* Coverage per set: **all 11! = 39,916,800 permutations**; every
  permutation is checked against the Electrum 2.x "standard" version tag
  (`HMAC-SHA512("Seed version", phrase)[0] == 0x01`); the ~155K survivors
  are derived with the Electrum KDF (salt `electrum`) at `m/0/0` with both
  encodings.
* Sets: midpoint-32, p5-no-next, p5-no-hint → 3 × 39.9M permutations.
* Results: **0 matches** in all three sets.
* Interpretation: no arrangement of the three strongest candidate word sets
  yields an Electrum-standard wallet whose first receiving address is the
  puzzle target. (Deeper Electrum indices m/0/1..4 / change addresses remain
  available via the `electrum` mode.)
* Cross-validation: the checksum-valid count over the midpoint set came out
  as **2,492,947**, matching the earlier independent Python enumeration
  exactly.

## 2026-11-24/25 — full no-checksum permutation scan (in progress)

* Binary: `scripts/experiments/nochecksum_scan.c` (mode `full`)
* Coverage: every permutation of the midpoint-32 set with the BIP39 KDF
  (salt `mnemonic`, empty passphrase) at `m/44'/0'/0'/0/0`, both encodings.
* Checkpoints: `results/scan/ncs.state.b*` (block = first-word position;
  offset = permutations within the 10! block). The scan resumes exactly
  where it stopped, so coverage is auditable to the permutation.
* Result so far: **0 matches** for the covered prefix (see the state files
  for the exact covered fraction and rate).

## Historical (re-verified from saved artefacts)

* Checksum-gated scan of the midpoint set (previous phase): 1,391,882 of
  2,492,947 checksum-valid permutations at the primary path (compressed) —
  0 matches. Reproducible from `results/scan/dset.valid` +
  `scripts/experiments/verify_valid.py`.
* Structured-permutation searches from phases 0–18 (7 fixed sets, 894,209
  arrangements, 55,584 checksum-valid, all address-tested at the primary
  path; 12,492,243 checksum-valid permutations counted but NOT all
  address-tested) — audited, not re-run in full here; see
  [PRIOR_EXPERIMENTS.md](PRIOR_EXPERIMENTS.md).

## 2026-11-25 — independent repository audit (Stage 0/1)

* Script/docs: `docs/REPO_AUDIT_2026-11-25.md`, `docs/KNOWN_ERRORS.md` §6–7.
* Local re-run results: `pip install -e '.[dev]'` OK; **72 tests passed
  then 74 after two new regression tests**; ruff 26 findings → **0**;
  baseline reproduction OK (story pin + wordlist sha match).
* Repo-level fixes: `scripts/` and `results/` trees + `.github/workflows/ci.yml`
  committed (they were missing from `main`, so README commands 404'd and CI
  never ran); CI hardened (strict lint, explicit input existence checks,
  non-masked smoke scan).

## 2026-11-25 — C-vs-Python cross-validation with positive control

* Script: `scripts/experiments/cross_validate.py` (+ new `derive` mode in
  `scripts/experiments/nochecksum_scan.c`).
* Coverage: 1000 deterministic vectors — 499 checksum-valid, 499
  checksum-invalid (shuffled), the Trezor vector, and 2 story natural
  orders — × 9 derivation paths × {compressed, uncompressed} hash160 =
  **18,000 values compared**.
* Result: **0 mismatches**; 0 hard derivation failures.
* Positive control: scanner copy with synthetic TARGET_H160 = the Trezor
  vector's own `m/44'/0'/0'/0/0` compressed hash160, run in `full` mode over
  the vector's own word file → **match fired and recorded exactly**
  (word indices [0×11, 3], path `m/44'/0'/0'/0/0`, compressed, BIP39 KDF).
  Negative control (disjoint words): no match file. Output:
  `results/scan/cross_validation.json`.

## 2026-11-25 — H1–H5 extraction-rule audit (story-side, deterministic)

* Script: `scripts/experiments/h1_h5_extraction_audit.py` (seed 20261125,
  2000-iteration null models). Output: `results/scan/h1_h5_audit.json`,
  `results/scan/h3_window_census.csv`.
* H1 (dream-anchored rules): 22 preregistered rules; 8 recover the held-out
  trio `maze`/`fury`/`renew`; **0 produce a complete 12-word set**.
* H2 (metatext instructions): all families rejected — no trio, wrong counts.
* H3 (grid/window): 50 of 481 32-token windows carry ≥ 12 distinct BIP39
  words; midpoint row ranks **48th**; 4 such windows even start at `echo`
  (tokens 1, 154, 173, 257); ±1-token sensitivity → 11 words; apostrophe
  tokenizer (509 tokens) → 8–9-word windows; frequency-preserving shuffle
  null p(any ≥ 12 window) = 1.0; joint anchor-alignment null p = 0.1305.
* H4 (¶5 mechanism): exactly 12 global-singleton BIP39 words in ¶5; +echo =
  13 → the drop-one choice (next vs hint) remains unmotivated.
* H5 (frequency): 15 once-in-each-half BIP39 words (the historical 11-word
  "set A" is exactly its ≥4-letter subset); null-A p = 0.409, null-B p = 1.0.

## 2026-11-25 — full no-checksum scan progress

* Checkpoint `results/scan/ncs.state.b0`: block 0 at offset **1,028,240 /
  3,628,800** (28.3% of block 0; cumulative permutations passed — the
  per-session `processed`/`derived` counters reset on resume, the `offset`
  is the authoritative progress), latest session 446,464 derivations,
  checksum-valid 27,863, **0 matches**, ~822 permutations/s, resumable.

## Validation of the tooling itself

* `selftest` mode: BIP39 official vector (Trezor vectors.json[0]), RIPEMD160
  known answer, golden permutations (8 × 2 paths, generated by the
  Python stack which itself matches the Trezor vectors and master xprv),
  and a 130-scalar differential test of the hand-written Montgomery
  secp256k1 against OpenSSL — all pass on every invocation.
* C-vs-Python differential (see above): 18,000 hash160 values, 0 mismatches,
  with a synthetic-positive match control proving the match path.
* Python test suite: **74 tests green** (tokenisation, positions, extraction
  registry, wordlist pins incl. the shade/shadow membership regression,
  BIP39/BIP32 vectors, address encodings, CLI).
