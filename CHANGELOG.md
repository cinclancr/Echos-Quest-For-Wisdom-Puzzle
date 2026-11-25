# Changelog

## 1.1.0 (2026-11-25) — independent repository audit

### Audit
- Repository made reproducible from a clean clone: the `scripts/` and
  `results/` trees and `.github/workflows/ci.yml` were missing from `main`
  (README commands 404'd, CI never ran) — committed; CI hardened (strict
  lint, input existence checks, non-masked smoke scan; documented in
  `docs/REPO_AUDIT_2026-11-25.md`).
- Factual fix: `shade` is NOT a BIP39 word (`shadow`, index 1574, is);
  corrected in `docs/HYPOTHESES.md` (hypothesis F) and locked by new
  regression tests (74 tests total; ruff: 26 findings → 0).
- New `derive` mode in the C scanner + `scripts/experiments/cross_validate.py`:
  1000 vectors (checksum-valid and -invalid) × 9 paths × 2 encodings =
  18,000 hash160 values C-vs-Python, 0 mismatches; synthetic-positive
  control fires correctly; negative control clean.
- New `scripts/experiments/h1_h5_extraction_audit.py`: preregistered
  dream-anchored rule battery (22 rules), metatext batteries, full
  32-token window census, paragraph-5 mechanism variants, and
  frequency/structure-preserving null models. Headline: the midpoint row is
  NOT statistically special (rank 48 of 481; joint-alignment null p = 0.13);
  the once-in-each-half richness is chance-level (p = 0.41).
- New `scripts/summarize_results.py` → `results/summary.json` (non-secret
  coverage counters, candidate-set IDs, artifact hashes).
- New docs: `docs/REPO_AUDIT_2026-11-25.md`, `docs/EXTRACTION_PRIORITY.md`;
  updated README, RESEARCH_STATUS, RESULTS, HYPOTHESES, SOLUTION,
  KNOWN_ERRORS (§6–7), HOW_TO_REPRODUCE.
- Second-pass remote sync (same day): re-diff against `main` after the
  reproducibility batch landed — published the remaining result fixtures
  (baseline summary, dset re-verification checkpoints, scanner log, the
  natural-order detail metadata) and 16 updated files (post-H4-audit
  state), corrected the pushed `LICENSE` attribution to
  `Copyright (c) 2026 cinclancr` and a YAML indentation bug in the
  new-hypothesis issue template (see
  `docs/REPO_AUDIT_2026-11-25.md` §7; full local verification re-run
  green: ruff clean, 74 tests passed, baseline KAT and C selftest
  `ALL OK`). The CI workflow file itself could not be published through
  the integration (missing *Workflows* permission — remediation in
  `docs/REPO_AUDIT_2026-11-25.md` §7.3; every other write succeeded).
- Story-copyright hygiene pass: the H1–H5 audit JSON no longer embeds the
  two verbatim story sentences (sentence index + sha256 only) and the
  baseline fixture no longer embeds the raw 32-token midpoint row
  (token count + row sha256 + the already-public filtered candidate
  list); both generators patched at the source, artifacts regenerated and
  re-verified statistically identical (rank 48, p = 0.1305/0.409/1.0).

### Research
- H4-audit battery extension: `p5-final-four`
  (`echo ancient into they more vivid night like maze fury renew hint`) —
  the only preregistered sentence-range rule reaching exactly 12 words —
  catalogued and battery-tested: 4 natural orders × 12 passphrases ×
  2 KDFs × 15 paths × 2 encodings = 2,880 comparisons, 0 matches.
  Natural-order battery is now 22 sets / **64,080 comparisons** (0 matches);
  brainwallet re-run at 22 sets / **176 comparisons** (0 matches).
- Checksum-valid re-verification against `dset.valid`: 1,533,194 of
  2,492,947 records address-tested (61.5%), 0 matches, resumable
  (checkpoint `dset_v3.json`).
- Full no-checksum scan of the midpoint-32 set: block 0 at 1,028,240 /
  3,628,800 (446,464 derivations), 0 matches, resumable.

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
  set scans (1.53M of 2.49M checksum-valid permutations address-tested,
  0 matches).
