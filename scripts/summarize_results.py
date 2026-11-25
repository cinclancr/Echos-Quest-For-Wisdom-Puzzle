#!/usr/bin/env python3
"""Consolidate results/ into results/summary.json (non-secret, 2026-11-25 audit).

Collects, with no key material:
* coverage counters from every C-scanner checkpoint state file,
* candidate-set identifiers with their exact word lists (public research
  data — these are failed candidates, not wallet secrets),
* natural-order battery and brainwallet counters,
* C-vs-Python cross-validation status,
* H1-H5 extraction audit headline statistics,
* artifact SHA-256 hashes and a timestamp,
* the global puzzle status (UNSOLVED — no address match anywhere).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCAN = REPO / "results" / "scan"

# stable IDs for the word sets the C scanner has scanned (word order in the
# file is the pinned first word + 11 others; all are public research data)
SET_FILES = {
    "midpoint-32": "words_dset.txt",
    "p5-no-hint": "words_p5_nohint.txt",
    "p5-no-next": "words_p5_nonext.txt",
}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    out: dict = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "UNSOLVED",
        "target_address": "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx",
        "status_note": "no derived address has ever matched the target "
                       "hash160 a6467f50...; no mnemonic is claimed",
    }

    # candidate sets
    sets = {}
    for set_id, fname in SET_FILES.items():
        p = SCAN / fname
        if p.is_file():
            words = p.read_text().split()
            sets[set_id] = {
                "file": f"results/scan/{fname}",
                "sha256": sha256_of(p),
                "first_word": words[0],
                "words": " ".join(words),
            }
    out["candidate_sets"] = sets

    # scanner checkpoint states (exact, auditable coverage)
    states = {}
    for st in sorted(SCAN.glob("*.state.b*")):
        try:
            states[st.name] = json.loads(st.read_text())
        except json.JSONDecodeError:
            continue
    out["c_scanner_checkpoints"] = states
    full_states = [v for v in states.values() if v.get("mode") == "full"]
    out["coverage_counters"] = {
        "full_mode_derived_total": sum(v.get("derived", 0) for v in full_states),
        "full_mode_block0_offset_of_3628800": (
            full_states[0].get("offset", 0) if full_states else 0),
        "full_mode_matches": sum(v.get("matches", 0) for v in full_states),
        "electrum1_matches": sum(v.get("matches", 0) for v in states.values()
                                  if v.get("mode") == "electrum1"),
        "electrum1_completed_blocks": sum(
            1 for v in states.values()
            if v.get("mode") == "electrum1" and v.get("complete") is True),
    }

    # natural-order battery + brainwallet (committed JSON summaries)
    for name, key in (("nochecksum_natural.json", "natural_order_battery"),
                      ("brainwallet_natural.json", "brainwallet_battery")):
        p = SCAN / name
        if p.is_file():
            d = json.loads(p.read_text())
            out["coverage_counters"][key] = {
                "sets": d.get("sets"), "comparisons": d.get("comparisons", 0),
                "matches": len(d.get("matches", [])) if isinstance(d.get("matches"), list) else d.get("matches"),
            }

    # cross-validation headline
    cv = SCAN / "cross_validation.json"
    if cv.is_file():
        d = json.loads(cv.read_text())
        out["cross_validation"] = {
            "vectors": d["vectors"],
            "rows_checked": d["rows_checked"],
            "mismatches": d["mismatches"],
            "positive_control_ok": d["positive_control"]["ok"],
            "negative_control_ok": d["negative_control"]["ok"],
            "c_source_sha256": d["c_source_sha256"],
        }

    # H1-H5 audit headline
    h15 = SCAN / "h1_h5_audit.json"
    if h15.is_file():
        d = json.loads(h15.read_text())
        out["h1_h5_audit"] = {
            "h1_rules_tested": d["h1_rule_count"],
            "h1_rules_recovering_dream_trio": d["h1_rules_recovering_trio"],
            "h1_complete_candidates": d["h1_candidates_complete"],
            "h3_windows_ge12_distinct_bip39": len(
                d["h3"]["window_census_32"]["windows_with_12_or_more"]),
            "h3_midpoint_rank": d["h3"]["window_census_32"]["rank_of_midpoint"],
            "h3_joint_alignment_null_echo": d["h3"]["null_joint_alignment"]["p_second_occurrence_window_ge12"]["echo"],
            "h5_once_each_half_bip39": d["h5"]["once_in_each_half"]["bip39_count"],
            "h5_null_a_p": d["h5"]["null_A_frequency_preserving_shuffle"]["p_value"],
            "h5_null_b_p": d["h5"]["null_B_sentence_order_shuffle"]["p_value"],
        }

    # artifact hashes
    artifacts = {}
    for rel in ("results/extractions.csv", "results/scan/h1_h5_audit.json",
                "results/scan/h3_window_census.csv",
                "results/scan/cross_validation.json",
                "results/scan/nochecksum_natural.json",
                "results/scan/brainwallet_natural.json"):
        p = REPO / rel
        if p.is_file():
            artifacts[rel] = sha256_of(p)
    out["artifact_sha256"] = artifacts

    dest = REPO / "results" / "summary.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k in ("status", "coverage_counters", "cross_validation",
                               "h1_h5_audit")}, indent=2, sort_keys=True))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
