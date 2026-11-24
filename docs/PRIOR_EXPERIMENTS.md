# Prior experiments (phases 0–18) — audited summary

The bundled `Echo_GLM53_Research_Context.zip` contained 18 phases of
Python/CSV experiments.  The audit below records what each phase actually
covered and which of its claims survived independent re-verification.

## Audited and CONFIRMED

* Tokenisation: 512 (dCode rule) / 509 (apostrophe rule) tokens — reproduced
  here by `python -m echoquest audit`.
* Anchor positions of echo/grace/shade/maze/fury/renew/cryptic — reproduced
  (see `data/expected_counts.json`).
* Midpoint row 257–288 contains 12 distinct BIP39 words — reproduced.
* Paragraph-5 singleton set (12 words) — reproduced.
* Cross-half singleton set, twice-and-four-letters set, parity set —
  reproduced in `results/extractions.csv`.
* The midpoint set has exactly 2,492,947 checksum-valid arrangements
  (reproduced TWICE independently: Python enumeration and the C scanner's
  counter over the complete space).
* Negative result: 894,209 structured permutations of seven fixed sets
  (55,584 checksum-valid) tested at the primary path — no match.  Bounded
  subsets were tested at 16 legacy paths with both encodings — no match.
* Negative result: 141,557 parity-set arrangements (8,890 checksum-valid)
  at the primary path — no match.
* 64 shortlisted checksum-valid candidates × 15 story passphrases × 9
  legacy paths × 2 encodings = 17,280 comparisons — no match (re-verified
  from the saved JSON).

## Audited and CORRECTED

* `armed`/`strong` BIP39 indices were wrong (97/1727 → 94/1721); several
  derived checksum counts changed after the fix (see KNOWN_ERRORS.md).
* Earlier "checksum passes" for 24 leave-one-out candidates: actual count 0,
  not 2. 648 structured arrangements: 43 passes, not 34.

## Audited and found UNVERIFIABLE/NOT RELIABLE

* ELS scans (~213K sequences), 540 Grace/Shade route combinations, 20K
  shuffled-split randomisations, four-letter orderings, row-9 path checks:
  negative results, treated as bounded historical leads (exact per-test
  coverage in the bundled CSVs; not re-run here).
* The C++ checksum-only count of 199,861,200 permutations (12,492,243
  valid): a count, NOT address derivations; not re-run here (the number is
  plausible: ~7 × 11! ≈ 280M with drop-one variants of smaller sets).
* The claim "3 Electrum-compatible standard prefixes" from midpoint-row
  permutations: unconfirmed; this project's own exhaustive Electrum-tag scan
  of the same set found zero matches at m/0/0 (deeper indices untested).

## What this phase added on top

* Removal of the checksum gate (natural orders: 61,200 comparisons; C
  scanner `full`/`electrum1` modes; validators fix).
* Brainwallet-style tests (168 comparisons) — negative.
* Exhaustive Electrum-standard permutation scans of the top three sets —
  negative at m/0/0.
* Independent C implementation with differential validation of every layer
  (PBKDF2 vs Trezor vector; secp256k1 vs OpenSSL; full-chain vs Python
  goldens), plus the reproducible test suite.
