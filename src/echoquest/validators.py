"""Candidate validation: checksum, seed, derivation and target comparison.

The :class:`CandidateReport` records exactly what was tested, with which
wordlist, derivation paths and passphrase, so no claim is unfalsifiable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .bip39 import mnemonic_valid, seed_from_mnemonic
from .electrum import electrum_seed_type, electrum_standard_addresses
from .wallet import address_for

TARGET_ADDRESS = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"

DEFAULT_PATHS = [
    "m/44'/0'/0'/0/0",
    "m/44'/0'/0'/0/1",
    "m/0'/0/0",
    "m/0'/0",
    "m/0/0",
    "m/0/0/0",
    "m",
    "m/49'/0'/0'/0/0",
    "m/84'/0'/0'/0/0",
]


@dataclass
class CandidateReport:
    """Validation record for one candidate mnemonic."""

    mnemonic: list[str]
    wordlist_valid: bool = False
    checksum_valid: bool = False
    passphrases: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    address_types: list[str] = field(default_factory=list)
    comparisons: int = 0
    target_match: str | None = None
    matched_path: str | None = None
    matched_passphrase: str | None = None
    electrum_type: str | None = None

    @property
    def as_dict(self) -> dict:
        return {
            "mnemonic_wordcount": len(self.mnemonic),
            "wordlist_valid": self.wordlist_valid,
            "checksum_valid": self.checksum_valid,
            "passphrases": self.passphrases,
            "paths": self.paths,
            "address_types": self.address_types,
            "comparisons": self.comparisons,
            "target_match": self.target_match,
            "matched_path": self.matched_path,
            "matched_passphrase": self.matched_passphrase,
            "electrum_type": self.electrum_type,
            "mnemonic_redacted": True,
        }


def validate_candidate(
    words: list[str],
    wordlist: list[str],
    passphrases: list[str] | None = None,
    paths: list[str] | None = None,
    target: str = TARGET_ADDRESS,
    address_types: list[str] | None = None,
    electrum: bool = True,
) -> CandidateReport:
    """Validate one candidate mnemonic: membership, checksum, addresses.

    Only 12-word candidates are derivable in BIP39; other lengths are
    reported without derivation.  Address derivation is read-only.
    """
    wl = set(wordlist)
    report = CandidateReport(mnemonic=list(words))
    report.wordlist_valid = all(w in wl for w in words)
    if len(words) == 12:
        report.checksum_valid = mnemonic_valid(words, wordlist)
        report.electrum_type = electrum_seed_type(" ".join(words))
    passphrases = [""] if passphrases is None else passphrases
    paths = DEFAULT_PATHS if paths is None else paths
    address_types = ["p2pkh"] if address_types is None else address_types
    report.passphrases = list(passphrases)
    # NOTE: derivation is intentionally NOT gated on checksum validity:
    # BIP39 seed derivation (PBKDF2) is well-defined for any 12 words, and a
    # puzzle author may own a wallet derived from a checksum-invalid phrase.
    if len(words) == 12:
        report.paths = list(paths)
        report.address_types = list(address_types)
        for pp in passphrases:
            seed = seed_from_mnemonic(words, pp)
            for path in paths:
                for at in address_types:
                    try:
                        addr = address_for(seed, path, at, compressed=True)
                    except Exception:
                        continue
                    report.comparisons += 1
                    if addr == target:
                        report.target_match = addr
                        report.matched_path = path
                        report.matched_passphrase = pp
                        return report
                    if at == "p2pkh":
                        try:
                            addr_u = address_for(seed, path, at, compressed=False)
                        except Exception:
                            continue
                        report.comparisons += 1
                        if addr_u == target:
                            report.target_match = addr_u
                            report.matched_path = f"{path} (uncompressed)"
                            report.matched_passphrase = pp
                            return report
        if electrum and not passphrases or electrum and passphrases == [""]:
            # Electrum treats BIP39 seeds as imported seeds (passphrase not used here).
            for pp in passphrases:
                addrs = electrum_standard_addresses(" ".join(words), pp, count=5, change_count=2)
                for a in addrs:
                    report.comparisons += 1
                    if a == target:
                        report.target_match = a
                        report.matched_path = "electrum-standard m/0/i|m/1/i"
                        report.matched_passphrase = pp
                        return report
    return report


def save_report(report: CandidateReport, out_path: str | Path) -> Path:
    """Write a redacted JSON report (mnemonic never stored)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.as_dict, indent=2) + "\n", encoding="utf-8")
    return out
