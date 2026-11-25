#!/usr/bin/env python3
"""Regenerate the reports under results/ from the current state.

* ``results/candidate_pools.csv``   — one row per candidate word pool
* ``results/method_ledger.csv``      — extraction methods with outcomes
* ``results/checksums_summary.csv``  — per-set checksum statistics of the
  natural orders (informational; derivation is NOT checksum-gated)
* ``results/scan_summary.json``      — consolidated C-scanner state

Requires the local story copy for the extraction catalogue.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echoquest import STORY_SHA256  # noqa: E402
from echoquest.extractors import list_methods, run  # noqa: E402
from echoquest.sources import load_story  # noqa: E402
from echoquest.tokenizers import tokenize  # noqa: E402
from echoquest.wordlists import load_wordlist  # noqa: E402

STORY = REPO / "private" / "story_original.txt"
RESULTS = REPO / "results"


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    if STORY.is_file():
        src = load_story(STORY, STORY_SHA256)
        tt = tokenize(src.text, "dcode")
        wl = load_wordlist()
        with (RESULTS / "method_ledger.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["method", "word_count", "words"])
            for m in list_methods():
                r = run(m, tt, wl)
                w.writerow([m, r.word_count, " ".join(r.words)])
        print(f"wrote {RESULTS / 'method_ledger.csv'}")
    else:
        print("story not found; skipped method ledger")

    # scanner state consolidation
    scan_dir = RESULTS / "scan"
    summary = {}
    if scan_dir.is_dir():
        for state in sorted(scan_dir.glob("*.state.b*")):
            try:
                data = json.loads(state.read_text())
            except json.JSONDecodeError:
                continue
            summary[state.name] = data
        (RESULTS / "scan_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"wrote {RESULTS / 'scan_summary.json'} ({len(summary)} blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
