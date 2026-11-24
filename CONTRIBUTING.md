# Contributing

Thank you for helping with the research.

## Ground rules

1. **Read-only wallet operations only.** Any code that can sign, broadcast
   or spend will not be accepted.
2. **No secrets, no story text.** `private/` is git-ignored on purpose; the
   story is not redistributed (see THIRD_PARTY_NOTICES.md).
3. **No fabricated results.** Report the exact derivation coverage of every
   experiment; "0 matches" is a result, not a failure.
4. **Pre-register extraction rules** before evaluating them (issue template
   "New extraction hypothesis").

## Development setup

```bash
python -m pip install -e '.[dev]'
pytest -q
ruff check src tests
```

C scanner:

```bash
gcc -O2 -Wno-deprecated-declarations -o scripts/experiments/nochecksum_scan \
    scripts/experiments/nochecksum_scan.c -lcrypto
scripts/experiments/nochecksum_scan selftest data/english.txt \
  results/scan/words_dset.txt results/scan/gt all 0 - results/scan/goldens_dset8.tsv
```

Any change touching derivation code must keep the selftest green (official
vectors + differential tests) and add regression tests for the fixed
behaviour.

## Pull requests

Use the PR template; small, verifiable commits preferred. Docs changes are
welcome — especially dated research-status updates with exact coverage.
