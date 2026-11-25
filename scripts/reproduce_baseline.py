#!/usr/bin/env python3
"""Reproduce the baseline research facts from the byte-exact story.

Verifies (from ``private/story_original.txt`` when present):
* SHA-256 provenance,
* both tokeniser conventions and their token counts,
* the positional facts that the extraction hypotheses are built on,
* the BIP39 wordlist pins.

Writes ``results/baseline_summary.json`` (the 32-token midpoint row is
stored as a SHA-256, not verbatim — see the story-copyright notice).
Read-only; deterministic.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echoquest import STORY_SHA256, TARGET_ADDRESS  # noqa: E402
from echoquest.sources import load_story  # noqa: E402
from echoquest.tokenizers import tokenize  # noqa: E402
from echoquest.wordlists import index_map, load_wordlist  # noqa: E402

STORY = REPO / "private" / "story_original.txt"


def main() -> int:
    if not STORY.is_file():
        print(f"story copy not found at {STORY}; see README (private/, git-ignored)")
        return 2
    src = load_story(STORY, STORY_SHA256)
    out = {
        "story_sha256": src.sha256,
        "story_sha256_matches_pin": src.sha256 == STORY_SHA256,
        "target_address": TARGET_ADDRESS,
    }
    for tok_name in ("dcode", "apostrophe"):
        tt = tokenize(src.text, tok_name)
        out[tok_name] = {
            "tokens": len(tt.tokens),
            "paragraphs": len(tt.paragraphs),
            "sentences": len(tt.sentences),
            "echo": tt.indices_of("echo"),
            "grace": tt.indices_of("grace"),
            "shade": tt.indices_of("shade"),
            "maze": tt.indices_of("maze"),
            "fury": tt.indices_of("fury"),
            "renew": tt.indices_of("renew"),
            "cryptic": tt.indices_of("cryptic"),
        }
    # midpoint row facts (dcode convention).  Story-copyright hygiene:
    # the 32 raw tokens are a contiguous verbatim story window, so the
    # published fixture stores only its length, its SHA-256 (verifiable by
    # anyone holding the hash-pinned story) and the FILTERED BIP39 candidate
    # list (already public research data) — never the raw row itself.
    tt = tokenize(src.text, "dcode")
    mid = [t for t in tt.tokens if 257 <= t.index <= 288]
    row_sha = hashlib.sha256(" ".join(t.text for t in mid).encode("utf-8")).hexdigest()
    out["midpoint_row_257_288"] = {
        "token_count": len(mid),
        "row_sha256": row_sha,
        "raw_tokens_redacted": True,
        "bip39_words_distinct": None,  # filled below
    }
    wl = load_wordlist()
    im = index_map(wl)
    midset = []
    for t in mid:
        if t.text in im and t.text not in midset:
            midset.append(t.text)
    out["midpoint_row_257_288"]["bip39_words_distinct"] = midset
    out["dream_word_indices"] = {w: im[w] for w in ("maze", "fury", "renew")}
    out["wordlist_sha256"] = hashlib.sha256((REPO / "data" / "english.txt").read_bytes()).hexdigest()
    dest = REPO / "results" / "baseline_summary.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
