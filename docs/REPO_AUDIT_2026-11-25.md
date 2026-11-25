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
* *Update (second pass, 2026-11-25):* the reproducibility batch landed on
  `main` (HEAD `9cedf61e56b7b31a5796dcda1fa3b9cd01fe9fef`), adding
  `scripts/` (15 files), `results/scan/` fixtures (46 files) and
  `results/{extractions.csv,summary.json}`. A re-diff against the local
  canonical tree then found the residue documented in §7 — most importantly
  `.github/workflows/ci.yml` was *still* absent and 13 files were stale
  relative to the post-H4-audit regenerated state.

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
  non-singletons; the **final-four variant is a formally complete 12-word
  candidate** (echo + dream trio + `ancient into they more vivid night
  like maze fury renew hint`) that was MISSING from the natural battery's
  catalogue — added and battery-tested during this audit (4 natural
  orders × 12 passphrases × 2 KDFs × 15 paths × 2 encodings, 0 matches;
  battery now 22 sets / 64,080 comparisons).
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
* Natural-order battery: 64,080 comparisons (22 sets after the H4 audit
  added `p5-final-four` — 12 passphrases × 15 paths × 2 encodings × 2 KDFs
  × the sets' natural orders; the number matches the committed
  `nochecksum_natural.json`). Brainwallet: 176 comparisons, 0 matches.
* Checksum-valid enumeration re-verification against `dset.valid`
  (2,492,947 records from the completed 39,916,800-permutation
  enumeration): checkpoint `dset_v3.json` records offset 1,533,194
  (61.5%), 0 matches so far, resumable (`dset_v1/v2/v3.json`,
  `dset_v3.log`).
* All counters above are machine-readable in `results/summary.json`.

## 6. Not done / not publishable

* The story text is third-party copyrighted and is **not** committed
  (users supply `private/story_original.txt`; hash-pin verified).
* The 59 MB `results/scan/dset.valid` (checksum-valid enumeration of an
  earlier phase) stays out of Git; its re-verification is documented in
  `docs/RESULTS.md` and reproducible via
  `scripts/experiments/enumerate_valid.py` + `verify_valid.py`.
* GitHub Actions had not yet executed the newly-pushed workflow at the
  first-pass time of writing; the second-pass push below (§7) carries the
  same `ci.yml` that passed locally end-to-end (selftest `ALL OK`, smoke
  scan exit 0), so the first green run was expected to be triggered by it.
* No mnemonic, private key, WIF, or recoverable wallet data appears in
  any public file. Puzzle status remains **UNSOLVED**.

## 7. Second-pass remote sync (2026-11-25)

A full blob-hash diff of the local canonical tree against `main`
(`9cedf61e`) found, before this pass: **119 of 132 remote files identical**;
15 local files unpublished; 13 remote files stale.

### 7.1 Story-copyright hygiene pass (new in this pass)

A pre-push leakage scan (normalised 60-char window containment against
`private/story_original.txt`) found verbatim story material in two result
artifacts:

* `results/scan/h1_h5_audit.json` embedded **two full sentences** — the
  dream sentence (twice: once in an `extra` field, once inside a `rule`
  label) and the "next morning" sentence (in `h4.context_next`);
* `results/baseline_summary.json` embedded the **full 32-token midpoint
  row** — a contiguous verbatim story window (~6% of the story).

Per the publication rule (never redistribute the story; short necessary
  quotes only) both generators were patched at the source and the
  artifacts regenerated:

* `scripts/experiments/h1_h5_extraction_audit.py`: sentence fields now
  carry `(sentence index, paragraph, sha256(sentence))` only;
* `scripts/reproduce_baseline.py`: the midpoint row is emitted as
  `token_count` + `row_sha256` + the filtered `bip39_words_distinct`
  candidate list (already public research data), never the raw tokens;
* both regenerated artifacts re-verified **statistically identical** to
  the previous run (9 headline statistics, including window-census rank
  48, joint-alignment p = 0.1305, null p-values 0.409/1.0 — determinism
  confirmed under the pinned seed) and **0 leaked 60-char runs**;
* `results/summary.json` regenerated → the `h1_h5_audit.json` artifact pin
  is now `a4c25060bdeb06594d32738d7e019c25c2e1cd6ee54a16f3c00862cd2e9d20de`.

Note for the maintainer: the *previously published* blob of
`h1_h5_audit.json` (in `main`'s history before this commit) still contains
the two sentences. History rewriting is out of scope by policy
(no force-push); the maintainer may decide whether a support request to
GitHub is warranted.

### 7.2 Re-verification run immediately before the push (same machine, fresh install)

| Command | Exact outcome |
|---|---|
| `python -m pip install -e '.[dev]'` | OK (echoquest-1.1.0, ruff-0.17.6) |
| `ruff check src/ scripts/ tests/` | `All checks passed!` (exit 0) |
| `CI=true python -m pytest` | **74 passed in 4.84s** (0 failed, 0 skipped; re-run after the hygiene pass) |
| `python scripts/reproduce_baseline.py` | exit 0 — story sha256 `437cb737…a5db0` matches pin; wordlist sha256 `2f5eed53…4dbda` matches pin; 512-token grid, 11/10/2 Echo/Grace/Shade markers, midpoint row and dream indices reproduced |
| `gcc -O2 -Wno-deprecated-declarations -o nochecksum_scan … -lcrypto` | builds clean |
| `nochecksum_scan selftest … goldens_dset8.tsv` | `ALL OK` — PBKDF2 KAT, RIPEMD160 KAT, Electrum m/0/0 golden, **16/16** golden permutations, **130/130** fast-EC vs OpenSSL |
| `nochecksum_scan full … 5` (smoke) | exit 0; `/tmp/smoke.state.b0` written, 8,192 derived, 0 matches |

### 7.3 CI workflow publication — blocked by the integration's permissions

Every push attempt that included `.github/workflows/ci.yml` failed with
`403 Resource not accessible by integration` (GitHub API), while every
push without a workflow file succeeded. The GitHub App/integration used
for publication lacks the **Workflows** permission, so workflow files
cannot be created or modified through it. Two remediation options for the
maintainer:

1. **Grant the permission:** GitHub → Settings → Applications (installed
   GitHub App) → repository access + permissions → enable
   *Workflows: read and write*. After that, re-publishing `ci.yml` (content
   reproduced below) will work through the same integration.
2. **Commit manually** (no permission change needed): create
   `.github/workflows/ci.yml` on `main` with exactly the content below
   (byte-exact local copy kept out of the API path; it is the same file
   that passed the full local verification of §7.2):

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: python -m pip install -e '.[dev]'
      - name: Lint (ruff, strict)
        run: ruff check src/ scripts/ tests/
      - name: Tests
        run: pytest -q
        env:
          # tests must never touch the network or any secret
          CI: "true"
      - name: Baseline reproduction (skips gracefully when story is git-ignored)
        # exit 0 = reproduced; exit 2 = story copy not present (expected in CI);
        # any other exit (including 127 command-not-found) fails the build
        run: |
          python scripts/reproduce_baseline.py
          rc=$?
          if [ $rc -ne 0 ] && [ $rc -ne 2 ]; then exit $rc; fi

  c-scanner:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify referenced inputs exist (fail loudly if not committed)
        run: |
          test -f scripts/experiments/nochecksum_scan.c
          test -f data/english.txt
          test -f results/scan/words_dset.txt
          test -f results/scan/goldens_dset8.tsv
      - name: Build and selftest the C scanner
        run: |
          sudo apt-get update -q && sudo apt-get install -y -q libssl-dev
          gcc -O2 -Wno-deprecated-declarations -o nochecksum_scan \
            scripts/experiments/nochecksum_scan.c -lcrypto
          ./nochecksum_scan selftest data/english.txt \
            results/scan/words_dset.txt results/scan/gt all 0 - \
            results/scan/goldens_dset8.tsv
      - name: Bounded smoke scan (5 seconds, read-only, must exit 0)
        run: |
          ./nochecksum_scan full data/english.txt results/scan/words_dset.txt \
            /tmp/smoke 0 5
          cat /tmp/smoke.state.b0
```

### 7.4 Actual publication record (commits on `main`)

| Commit | Content |
|---|---|
| `fc67765f` | LICENSE attribution fix; issue-template YAML fix; `tests/test_wordlist.py` normalisation |
| `4cae2e7b` | `results/scan/dset_v1.json` |
| `db11bcc7` | `dset_v2.json`, `dset_v3.json`, `dset_v3.log`, `ncs_wA.log` |
| `4f28c2a5` | `scripts/reproduce_baseline.py` (redaction patch) + redacted `results/baseline_summary.json` |
| `eaa7b924` | `scripts/experiments/nochecksum_natural_orders.py` (shade fix + `p5-final-four`) |
| `8a242e4b` | `scripts/experiments/h1_h5_extraction_audit.py` (redaction patch) — blob-verified byte-exact |
| `6064ed0d` | *accidental partial artifact*: a truncated placeholder of `h1_h5_audit.json` (valid JSON, missing most sections) — an API-retry mistake, immediately superseded |
| `802a2d43` | full redacted `results/scan/h1_h5_audit.json` — blob-verified byte-exact (`a1a5928b…`), fixes `6064ed0d` |
| `2ca84de5` | `results/summary.json` (pins the redacted audit artifact; 64,080/22/176 counters) — blob-verified |
| `3ab8cb44` | `README.md` (accurate CI-permission caveat, 64,080/22-set battery numbers) |
| `c7e2de4c` | `docs/RESULTS.md` + `docs/RESEARCH_STATUS.md` (accurate CI note, battery numbers) |
| `1d3378a2` | `docs/EXTRACTION_PRIORITY.md` (post-audit ranking incl. the H4 p5-final-four finding) |
| `c138c4be` | `results/extractions.csv` (27-method extraction catalogue, corrected marker-parity row) |
| `5c95cd53` | `results/scan/h3_window_census.csv` (481 windows, midpoint rank 48) |
| `c07268bb` | `results/scan/nochecksum_natural_detail.jsonl` (89 per-set/per-order records, positions + flags only) |
| `ac85fccd` | `CHANGELOG.md` (accurate CI-permission note, battery numbers, hygiene-pass entry) |
| *this commit* | `docs/REPO_AUDIT_2026-11-25.md` (final corrected record — this file) |

Every pushed artifact larger than a few KB was verified byte-exact by
comparing the remote blob SHA-1 with the local file's git blob SHA.

Files published by this pass (net of the above commits):

* **Added:** `results/baseline_summary.json` (redacted form),
  `results/scan/dset_v1.json`, `dset_v2.json`, `dset_v3.json`,
  `dset_v3.log`, `ncs_wA.log`, `results/scan/nochecksum_natural_detail.jsonl`
  (per-set order metadata only — positions and flags).
* **Updated:** `LICENSE` (attribution corrected to the master-prompt form
  `Copyright (c) 2026 cinclancr`; the pushed copy had used the account's
  display name — flagged as an anomaly by this pass),
  `.github/ISSUE_TEMPLATE/new_hypothesis.yml` (YAML indentation bug:
  `validations:` was nested under `attributes:`), `README.md`,
  `CHANGELOG.md`, `docs/EXTRACTION_PRIORITY.md`, `docs/RESEARCH_STATUS.md`,
  `docs/RESULTS.md`, this file, `results/extractions.csv`,
  `results/summary.json`, `results/scan/h1_h5_audit.json` (redacted per
  §7.1), `results/scan/h3_window_census.csv`,
  `scripts/experiments/nochecksum_natural_orders.py` (shade comment fix +
  the `p5-final-four` set), `scripts/experiments/h1_h5_extraction_audit.py`
  (redaction patch per §7.1), `scripts/reproduce_baseline.py` (redaction
  patch per §7.1), `tests/test_wordlist.py` (trailing-newline
  normalisation only).
* **Deliberately not published:** `.github/workflows/ci.yml` (permission
  block — see §7.3 for the content and remediation),
  `results/scan/dset.valid` (59 MB, git-ignored by design), the
  Electrum progress logs `elc_dset.progress`, `elc_p5nohint.progress`,
  `elc_p5nonext.progress` (redundant with the already-published
  `elc_*.state.b*` checkpoint files), the empty placeholder logs
  `dset_v4.log`, `elc_dset.log`, `workerB_outer.log` (0 bytes),
  `private/story_original.txt` and everything else under `private/`.

Post-push acceptance check: remote tree re-listed; pushed paths verified
present with byte-exact content (blob SHA comparison). **CI has still
never executed** (the workflow file is not on `main`); until §7.3 is
acted on, the verification status of record remains the local §7.2 run.
