"""Hypothesis ledger: append-only JSONL/CSV record of tested hypotheses.

Every experiment appends one row per (hypothesis, parameter set) with the
raw output, validity flags and reproduction command, so repeated or failed
leads are never silently re-tested.
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATUS_TAGS = ("VERIFIED", "HYPOTHESIS", "UNTESTED", "REJECTED", "INCOMPLETE")


@dataclass
class LedgerEntry:
    """One tested hypothesis row."""

    id: str
    rule: str
    carrier: str
    parameters: str
    raw_output: str
    bip39_membership: str
    checksum: str
    derivation_paths: str
    target_match: str
    reason: str
    reproduction_command: str
    status: str
    source_evidence: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class Ledger:
    """Append-only ledger writing JSONL + mirrored CSV."""

    def __init__(self, jsonl_path: str | Path, csv_path: str | Path | None = None) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.csv_path = Path(csv_path) if csv_path else self.jsonl_path.with_suffix(".csv")
        self.entries: list[LedgerEntry] = []
        self._seen_ids: set[str] = set()

    def add(
        self,
        entry_id: str,
        rule: str,
        carrier: str,
        parameters: str,
        raw_output: str,
        bip39_membership: str,
        checksum: str,
        derivation_paths: str,
        target_match: str,
        reason: str,
        reproduction_command: str,
        status: str,
        source_evidence: str,
    ) -> LedgerEntry:
        """Append an entry (duplicated ids are rejected)."""
        if entry_id in self._seen_ids:
            raise ValueError(f"duplicate ledger id: {entry_id}")
        if status not in STATUS_TAGS:
            raise ValueError(f"invalid status {status!r}; expected one of {STATUS_TAGS}")
        entry = LedgerEntry(
            id=entry_id,
            rule=rule,
            carrier=carrier,
            parameters=parameters,
            raw_output=raw_output,
            bip39_membership=bip39_membership,
            checksum=checksum,
            derivation_paths=derivation_paths,
            target_match=target_match,
            reason=reason,
            reproduction_command=reproduction_command,
            status=status,
            source_evidence=source_evidence,
        )
        self.entries.append(entry)
        self._seen_ids.add(entry_id)
        return entry

    def flush(self) -> None:
        """Write JSONL and CSV artefacts."""
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(asdict(e)) + "\n")
        if not self.entries:
            return
        fieldnames = list(asdict(self.entries[0]).keys())
        new_file = not self.csv_path.exists()
        with self.csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if new_file:
                writer.writeheader()
            for e in self.entries:
                writer.writerow(asdict(e))
        self.entries = []
