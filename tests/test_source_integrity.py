"""Source integrity: byte-exact provenance handling.

Uses the committed synthetic fixture (NOT the copyrighted puzzle story) so
the tests run in CI without redistributing third-party text.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from echoquest.sources import SourceIntegrityError, load_story, record_provenance

DATA = Path(__file__).resolve().parents[1] / "data"
FIXTURE = DATA / "synthetic_fixture.txt"
FIXTURE_SHA256 = "a90833bcffd70afca2a25dc586091ab41727808b28f5dcea5cf233763b7233c6"


def test_fixture_hash_is_stable() -> None:
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256


def test_load_story_with_matching_hash() -> None:
    src = load_story(FIXTURE, expect_sha256=FIXTURE_SHA256)
    assert src.sha256 == FIXTURE_SHA256
    assert "Echo's Test Fixture" in src.text


def test_load_story_with_wrong_hash_raises() -> None:
    with pytest.raises(SourceIntegrityError):
        load_story(FIXTURE, expect_sha256="00" * 32)


def test_load_story_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_story(DATA / "no_such_file.txt")


def test_provenance_record_has_no_story_content() -> None:
    src = load_story(FIXTURE)
    rec = record_provenance(src, origin_url="https://example.invalid/x", note="synthetic")
    assert "Echo's Test Fixture" not in str(rec)
    assert rec["sha256"] == FIXTURE_SHA256
