"""Pinned BIP39 English wordlist: integrity anchors.

Guards against the historical hand-curated index bug (armed/strong were
mis-indexed in phases before 18).
"""

from __future__ import annotations

from pathlib import Path

from echoquest.wordlists import WORDLIST_URL, index_map, load_wordlist

WL_PATH = Path(__file__).resolve().parents[1] / "data" / "english.txt"
EXPECTED_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"


def test_wordlist_size_and_uniqueness() -> None:
    wl = load_wordlist(WL_PATH)
    assert len(wl) == 2048
    assert len(set(wl)) == 2048


def test_wordlist_pinned_hash() -> None:
    import hashlib

    assert hashlib.sha256(WL_PATH.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_known_index_anchors() -> None:
    wl = load_wordlist(WL_PATH)
    im = index_map(wl)
    # regression: an earlier phase used armed=97 / strong=1727 (wrong).
    assert im["armed"] == 94
    assert im["strong"] == 1721
    # dream words and the pinned first word.
    assert im["maze"] == 1100
    assert im["fury"] == 755
    assert im["renew"] == 1457
    assert im["echo"] == 559


def test_official_vector_words_present() -> None:
    wl = load_wordlist(WL_PATH)
    for w in ("abandon", "about", "legal", "winner", "thank", "yellow"):
        assert w in wl


def test_shade_is_not_a_bip39_word_shadow_is() -> None:
    """Regression for the docs/HYPOTHESES.md shade error (audit 2026-11-25).

    The official English BIP39 list contains ``shadow`` (index 1574, 0-based)
    but does NOT contain ``shade``.  Any hypothesis claiming the literal
    story token ``shade`` is a BIP39 word is factually wrong; the only
    BIP39-compatible reading is the prefix completion shade->shadow, which
    must be flagged as an explicit, unmotivated-by-text transformation.
    """
    wl = load_wordlist(WL_PATH)
    im = index_map(wl)
    assert "shade" not in wl
    assert "shade" not in im
    assert "shadow" in wl
    assert im["shadow"] == 1574


def test_midpoint_and_p5_words_membership_is_exact() -> None:
    """Exact membership (not prefix expansion) for every catalogued word.

    Members of the story-derived candidate sets that are NOT BIP39 words:
    after (midpoint row), nothing/next are BIP39 (checked), etc.  This locks
    the exact-membership rule used by all extractors.
    """
    wl = set(load_wordlist(WL_PATH))
    midpoint_row_words = {
        "echo", "more", "vivid", "night", "like", "maze", "fury", "renew",
        "hint", "what", "they", "upon", "after",
    }
    non_members = {w for w in midpoint_row_words if w not in wl}
    assert non_members == {"after"}, sorted(non_members)



def test_verify_flag_rejects_tampered_file(tmp_path) -> None:
    bad = tmp_path / "bad.txt"
    lines = WL_PATH.read_text("utf-8").splitlines()
    lines[0] = "abando"  # corrupt one word
    bad.write_text("\n".join(lines) + "\n", "utf-8")
    import pytest

    from echoquest.wordlists import WordlistError

    with pytest.raises(WordlistError):
        load_wordlist(bad, verify=True)


def test_wordlist_url_is_the_official_source() -> None:
    assert WORDLIST_URL.endswith("bitcoin/bips/master/bip-0039/english.txt")
