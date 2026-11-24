# Changelog

## 1.0.0 (2026-11-25)

### Research
- Removed the checksum gate from all candidate derivation (maintainer
  insight: the hidden phrase may be checksum-invalid; PBKDF2 does not care).
- Natural-order no-checksum battery: 21 sets x 12 passphrases x 2 KDFs x
  15 paths x 2 encodings = 61,200 comparisons — 0 matches.
- Brainwallet-style natural orders: 168 comparisons — 0 matches.
- Electrum-standard-tag permutation scans (all 11! arrangements) of the
  midpoint-32, p5-no-next and p5-no-hint sets at m/0/0 — 0 matches each;
  checksum-valid counter cross-validates the earlier Python enumeration
  exactly (2,492,947).
- Full no-checksum permutation scan of the midpoint-32 set (BIP39 KDF,
  m/44'/0'/0'/0/0, both encodings) launched with checkpointing; coverage
  documented in results/scan.

### Toolkit
- C scanner `scripts/experiments/nochecksum_scan.c`: modes selftest / full /
  electrum1 / electrum; hand-written Montgomery secp256k1 (differential-
  tested vs OpenSSL); fast PBKDF2 with cached ipad/opad midstates; exact
  itertools-compatible enumeration; checkpoint/resume; match records as
  word indices only.
- `echoquest.validators` no longer gates derivation on checksum validity.

### Repository
- Full documentation set (docs/), test suite (72 tests), CI workflow,
  issue templates, community health files, provenance and licensing notes.

## 0.x (2026-11-23/24) — pre-release

- Core toolkit: tokenisers, positions, extractors, BIP39/BIP32/Electrum
  wallet modules, CLI.
- Checksum-gated permutation enumeration + verification scripts; midpoint
  set scans (1.39M of 2.49M checksum-valid permutations address-tested,
  0 matches).
