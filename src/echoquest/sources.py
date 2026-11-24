"""Source provenance: byte-exact story input handling.

The puzzle story is copyrighted third-party material supplied for private
analysis.  This module only ever *verifies* and *reads* such files; it never
mutates them.  The public repository must not redistribute the story; users
place their legally obtained copy under ``private/`` (git-ignored).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


class SourceIntegrityError(ValueError):
    """Raised when a source file does not match its expected provenance."""


@dataclass(frozen=True)
class StorySource:
    """A byte-verified story source."""

    path: Path
    raw: bytes
    sha256: str

    @property
    def text(self) -> str:
        """Decode as UTF-8 (the source is plain ASCII)."""
        return self.raw.decode("utf-8")


def load_story(path: str | Path, expect_sha256: str | None = None) -> StorySource:
    """Load a story file and (optionally) verify its SHA-256.

    Parameters
    ----------
    path:
        Filesystem path of the story text.
    expect_sha256:
        Expected hex digest.  When ``None`` no check is performed (the
        caller asserts provenance separately); when provided a mismatch
        raises :class:`SourceIntegrityError`.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"story file not found: {p}")
    raw = p.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expect_sha256 is not None and digest != expect_sha256.lower():
        raise SourceIntegrityError(
            f"story SHA-256 mismatch: expected {expect_sha256}, got {digest}"
        )
    return StorySource(path=p, raw=raw, sha256=digest)


def record_provenance(source: StorySource, origin_url: str, note: str) -> dict:
    """Build a JSON-serialisable provenance record (no story content)."""
    return {
        "file": source.path.name,
        "size_bytes": len(source.raw),
        "sha256": source.sha256,
        "origin_url": origin_url,
        "note": note,
        "redistribution": "not permitted without rights-holder consent",
    }


def save_provenance(source: StorySource, out_path: str | Path, origin_url: str, note: str) -> Path:
    """Write a provenance JSON record (contains hashes only, no story text)."""
    payload = record_provenance(source, origin_url, note)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
