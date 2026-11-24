# Known errors — and their fixes

Historical mistakes found during the independent audit of the earlier
research phases, all now corrected and locked by regression tests.

## 1. BIP39 index mis-entries (`armed`, `strong`) — FIXED

* Earlier phases hand-entered `armed=97` and `strong=1727`.
* Correct (verified against the pinned official wordlist): `armed=94`,
  `strong=1721`.
* Consequence in earlier phases: 24 leave-one-out candidates wrongly showed
  "2 checksum passes" (actually 0); arrangement pass counts were wrong.
* Fixed by: `scripts/audit_legacy_indices.py`, regression-locked in
  `tests/test_wordlist.py` and `tests/test_known_regressions.py`.

## 2. Checksum gating of the address search — FIXED (2026-11-24)

* All previous address derivation was gated on BIP39 checksum validity,
  covering only 1/16 of the arrangement space.  The maintainer's insight:
  the author's phrase may be checksum-invalid (derivation works anyway).
* Fixed by: the no-checksum battery (`nochecksum_natural_orders.py`), the
  removal of the gate in `echoquest.validators.validate_candidate`, and
  the C scanner modes `full`/`electrum1`.

## 3. Python-implementation memory bugs during C development — FIXED

While porting the scan to C, three bugs were found and fixed by differential
listing against OpenSSL/Python (this is why the selftest exists):

* fe_mul REDC: an 8-limb accumulator dropped the rare q ≥ 2^256 overflow
  (~19% of random inputs failed) — fixed with a 9-limb accumulator and a
  second conditional subtraction; fuzz-tested on 500+ random pairs vs Python.
* fe_inv: the exponentiation accumulator started at plain `1` instead of
  Mont(1), and processed exponent bits LSB-first with an MSB-first ladder
  (reversing the exponent bits) — fixed; verified against `pow(5,-1,p)`.
* j_madd: a mis-transcribed mixed-addition formula (wrong H sign) —
  replaced with a hand-derived formula verified numerically; the full
  `fast_pub` pipeline now matches OpenSSL on 1000+ scalars.

## 4. "Checksum-valid" confusion in prior reports — CLARIFIED

* A prior C++ run counted 12,492,243 checksum-valid permutations of seven
  fixed sets but did NOT address-test them all; earlier summaries sometimes
  blurred "tested" vs "counted".  All coverage statements in this
  repository now distinguish exact derivation counts from checksum counts.

## 5. Claimed-but-unverified prior "successes" — REJECTED

* No earlier phase produced an address match; any hint of a "solved
  mnemonic" in intermediate notes was coincidence (checksum-valid
  rearrangements occur at 1/16 by chance and are not evidence).  The
  puzzle remains UNSOLVED; see SOLUTION.md.
