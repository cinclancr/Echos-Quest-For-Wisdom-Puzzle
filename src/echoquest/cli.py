"""Command line interface: ``python -m echoquest``.

Commands
--------
ingest          verify a story copy byte-for-byte (SHA-256)
audit           tokenisation and positional audit (both tokenisers)
positions       write the full positional table CSV
extract         run one or all extraction hypotheses
list-methods    list registered extraction methods
test-candidate  validate a 12-word candidate file (checksum/paths, redacted)
verify          verify candidates against the target address (read-only)
hypotheses      list the hypothesis ledger families and statuses
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import STORY_SHA256, TARGET_ADDRESS, __version__
from .bip39 import mnemonic_valid, seed_from_mnemonic
from .extractors import list_methods, run
from .positions import write_positions_csv
from .reporting import write_extraction_csv, write_json
from .sources import load_story
from .tokenizers import TOKENIZERS, tokenize
from .validators import validate_candidate
from .wordlists import load_wordlist

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORY = REPO_ROOT / "private" / "story_original.txt"


def _cmd_ingest(args: argparse.Namespace) -> int:
    try:
        source = load_story(args.input, args.sha256 or STORY_SHA256)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {source.path}")
    print(f"size: {len(source.raw)} bytes")
    print(f"sha256: {source.sha256}")
    if args.sha256 is None:
        print(f"expected (pinned): {STORY_SHA256}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    try:
        source = _load_pinned_or_free(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report: dict = {"source_sha256": source.sha256, "tokenizers": {}}
    for name in TOKENIZERS:
        tt = tokenize(source.text, name)
        counts = tt.counts()
        info = {
            "tokens": len(tt.tokens),
            "paragraphs": len(tt.paragraphs),
            "sentences": len(tt.sentences),
            "paragraph_token_counts": [p.token_count for p in tt.paragraphs],
            "sentence_token_counts": [s.token_count for s in tt.sentences],
            "echo_positions": tt.indices_of("echo"),
            "grace_positions": tt.indices_of("grace"),
            "shade_positions": tt.indices_of("shade"),
            "maze_position": tt.indices_of("maze"),
            "fury_position": tt.indices_of("fury"),
            "renew_position": tt.indices_of("renew"),
            "cryptic_positions": tt.indices_of("cryptic"),
            "counts": {
                w: counts.get(w, 0)
                for w in ("echo", "grace", "shade", "of", "to", "the", "a", "and", "like")
            },
        }
        report["tokenizers"][name] = info
    print(json.dumps(report, indent=2))
    if args.output:
        write_json(report, args.output)
    return 0


def _load_pinned_or_free(args: argparse.Namespace):
    """Load the story pinned by default; ``--sha256 none`` accepts any text."""
    expected = getattr(args, "sha256", None)
    if expected == "none":
        expected = None
    elif expected is None:
        expected = STORY_SHA256
    return load_story(args.input, expected)


def _cmd_positions(args: argparse.Namespace) -> int:
    try:
        source = _load_pinned_or_free(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    tt = tokenize(source.text, args.tokenizer)
    out = write_positions_csv(tt, args.output)
    print(f"wrote {len(tt.tokens)} rows to {out}")
    return 0


def _cmd_extract(args: argparse.Namespace) -> int:
    try:
        source = _load_pinned_or_free(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    tt = tokenize(source.text, args.tokenizer)
    wl = load_wordlist(args.wordlist)
    methods = [args.method] if args.method != "all" else list_methods()
    results = []
    for m in methods:
        res = run(m, tt, wl)
        results.append(res)
        print(f"[{res.method}] {res.word_count} words: {' '.join(res.words)}")
        if res.notes:
            print(f"    note: {res.notes}")
    if args.output:
        write_extraction_csv(results, args.output)
        print(f"wrote {args.output}")
    return 0


def _cmd_list_methods(_args: argparse.Namespace) -> int:
    for m in list_methods():
        print(m)
    return 0


def _cmd_hypotheses(_args: argparse.Namespace) -> int:
    from .hypotheses import all_hypotheses

    for h in all_hypotheses():
        print(f"[{h.status}] {h.hid} ({h.family}): {h.summary}")
    return 0


def _read_candidate_file(path: str) -> list[list[str]]:
    candidates = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        candidates.append(line.split())
    return candidates


def _cmd_test_candidate(args: argparse.Namespace) -> int:
    wl = load_wordlist(args.wordlist)
    for words in _read_candidate_file(args.candidate_file):
        valid = mnemonic_valid(words, wl)
        print(f"{'VALID' if valid else 'INVALID':7s} checksum for {len(words)}-word candidate")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    wl = load_wordlist(args.wordlist)
    passphrases = [""]
    if args.passphrase_file:
        passphrases = [
            line.rstrip("\n").strip()
            for line in Path(args.passphrase_file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    reports = []
    matched = False
    for words in _read_candidate_file(args.candidate_file):
        if len(words) != 12:
            print(f"skip: candidate with {len(words)} words (only 12-word candidates derivable)")
            continue
        rep = validate_candidate(words, wl, passphrases=passphrases)
        reports.append(rep.as_dict)
        if rep.target_match:
            matched = True
            print(f"MATCH: target address matched (path {rep.matched_path}) — see report")
        else:
            print(
                f"no match: checksum={'valid' if rep.checksum_valid else 'invalid'} "
                f"comparisons={rep.comparisons}"
            )
    out = write_json(
        {
            "target": TARGET_ADDRESS,
            "matches": sum(1 for r in reports if r.get("target_match")),
            "reports": reports,
        },
        args.output,
    )
    print(f"wrote redacted report {out}")
    return 0 if not matched else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echoquest", description="Echo's Quest For Wisdom research toolkit")
    parser.add_argument("--version", action="version", version=f"echoquest {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="verify a story copy byte-for-byte")
    p.add_argument("--input", default=str(DEFAULT_STORY))
    p.add_argument("--sha256", default=None, help="expected SHA-256 (default: pinned research hash)")
    p.set_defaults(func=_cmd_ingest)

    p = sub.add_parser("audit", help="tokenisation and positional audit")
    p.add_argument("--input", default=str(DEFAULT_STORY))
    p.add_argument("--sha256", default=None, help="expected SHA-256; 'none' disables pinning")
    p.add_argument("--output", default=None)
    p.set_defaults(func=_cmd_audit)

    p = sub.add_parser("positions", help="write the full positional table")
    p.add_argument("--input", default=str(DEFAULT_STORY))
    p.add_argument("--sha256", default=None, help="expected SHA-256; 'none' disables pinning")
    p.add_argument("--tokenizer", default="dcode", choices=TOKENIZERS)
    p.add_argument("--output", default="results/positions.csv")
    p.set_defaults(func=_cmd_positions)

    p = sub.add_parser("extract", help="run extraction hypotheses")
    p.add_argument("--input", default=str(DEFAULT_STORY))
    p.add_argument("--sha256", default=None, help="expected SHA-256; 'none' disables pinning")
    p.add_argument("--tokenizer", default="dcode", choices=TOKENIZERS)
    p.add_argument("--method", default="all", help=f"one of: {', '.join(list_methods())} or all")
    p.add_argument("--wordlist", default=None)
    p.add_argument("--output", default=None)
    p.set_defaults(func=_cmd_extract)

    p = sub.add_parser("list-methods", help="list extraction methods")
    p.set_defaults(func=_cmd_list_methods)

    p = sub.add_parser("hypotheses", help="list hypothesis families and statuses")
    p.set_defaults(func=_cmd_hypotheses)

    p = sub.add_parser("test-candidate", help="checksum-validate candidate files")
    p.add_argument("--candidate-file", required=True)
    p.add_argument("--wordlist", default=None)
    p.set_defaults(func=_cmd_test_candidate)

    p = sub.add_parser("verify", help="verify candidates against the target address (read-only)")
    p.add_argument("--candidate-file", required=True)
    p.add_argument("--wordlist", default=None)
    p.add_argument("--passphrase-file", default=None)
    p.add_argument("--output", default="results/verification-redacted.json")
    p.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
