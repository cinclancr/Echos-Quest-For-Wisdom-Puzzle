"""Reporting helpers: CSV/JSON artefacts for extraction results."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .extractors import ExtractionResult


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_extraction_csv(results: list[ExtractionResult], out_path: str | Path) -> Path:
    """Write extraction results to CSV."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["method", "description", "word_count", "words", "positions", "prefixes_used", "notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r.as_row)
    return out


def write_json(data: object, out_path: str | Path) -> Path:
    """Write a JSON artefact with an injected UTC timestamp."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, dict):
        data = {"generated_utc": timestamp_utc(), **data}
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return out
