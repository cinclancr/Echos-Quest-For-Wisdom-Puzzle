# How to reproduce

Every command below was used to produce the results in this repository.
All operations are read-only (address derivation and comparison only).

## 0. Environment

* Python ≥ 3.10 with `cryptography` (`pip install -e '.[dev]'`)
* A C compiler + OpenSSL ≥ 3.0 for the fast scanner
* ~150 MB free disk for scan states

## 1. Source and wordlist integrity

```bash
# place your legally obtained story copy at private/story_original.txt
python -m echoquest ingest --input private/story_original.txt \
    --sha256 437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0

# wordlist pin + critical index audit (armed=94, strong=1721, ...)
python scripts/audit_legacy_indices.py
```

## 2. Baseline positional facts

```bash
python scripts/reproduce_baseline.py       # writes results/baseline_summary.json
python -m echoquest audit --input private/story_original.txt
python -m echoquest positions --input private/story_original.txt --output results/positions.csv
python -m echoquest extract --input private/story_original.txt --method all --output results/extractions.csv
```
(Outputs verified: 512 tokens dCode / 509 apostrophe; echo at
[1,74,154,173,226,257,300,342,376,412,444]; shade at [14,494].)

## 3. Test suite (no network, no secrets)

```bash
pytest -q                     # 72 tests: vectors, tokenizers, CLI, regressions
```

## 4. Candidate verification (read-only, no checksum gate)

```bash
# one 12-word candidate per line in private/candidates.txt
python -m echoquest verify --candidate-file private/candidates.txt \
    --output results/verification-redacted.json
python scripts/verify_target.py --candidate-file private/candidates.txt --json
```

## 5. The C permutation scanners

```bash
gcc -O2 -Wno-deprecated-declarations -o scripts/experiments/nochecksum_scan \
    scripts/experiments/nochecksum_scan.c -lcrypto

# selftest (BIP39 vectors, goldens, fast-EC vs OpenSSL differential)
scripts/experiments/nochecksum_scan selftest data/english.txt \
    results/scan/words_dset.txt results/scan/gt all 0 - results/scan/goldens_dset8.tsv
```

Words files are 12 lines, first line = `echo` (pinned). The 11! space splits
into 11 blocks by the position of the first unknown word.

```bash
# full no-checksum scan (BIP39 KDF, m/44'/0'/0'/0/0, both encodings):
# worker A: blocks 0..4   worker B: blocks 5..10
scripts/experiments/nochecksum_scan full data/english.txt \
    results/scan/words_dset.txt results/scan/ncs 0,1,2,3,4 0 &
scripts/experiments/nochecksum_scan full data/english.txt \
    results/scan/words_dset.txt results/scan/ncs 5,6,7,8,9,10 0 &

# Electrum-standard-tag filtered scan (Electrum KDF, m/0/0):
scripts/experiments/nochecksum_scan electrum1 data/english.txt \
    results/scan/words_dset.txt results/scan/elc_dset 0,1,2,3,4,5,6,7,8,9,10 0
```

* Checkpoints appear as `results/scan/<prefix>.state.b<block>`; interrupted
  runs resume automatically at the exact permutation offset.
* Any match is appended to `<prefix>.match` as word indices + parameters.
* A bounded time budget can be given instead of `0` (seconds).

## 6. Historical (checksum-gated) scans, reproduced

```bash
# enumerate all checksum-valid permutations of the midpoint set (phase A)
python scripts/experiments/enumerate_valid.py --set \
    "more,vivid,night,like,maze,fury,renew,hint,they,what,upon" \
    --out results/scan/dset.valid
# address-test slices of them (phase B)
python scripts/experiments/verify_valid.py --valid-file results/scan/dset.valid \
    --paths "m/44'/0'/0'/0/0" --offset 0 --count 100000
```

## 7. Regenerating reports

```bash
python scripts/regenerate_reports.py    # method ledger + scanner states
python scripts/run_phase18.py           # corrected paragraph-5 checks
```

## Notes on interpretation

* A "0 matches" row means exactly: within the stated coverage, no derivation
  produced the target hash160. It never proves non-existence outside that
  coverage.
* The enumeration order of the C scanner matches Python
  `itertools.permutations(unknowns)` with the input order of the words file,
  so results are directly comparable across implementations.
