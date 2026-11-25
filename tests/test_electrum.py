"""Electrum seed format algorithms (read-only).

Anchors verified against the upstream Electrum source behaviour; the
classification phrase below was found by an exhaustive wordlist search in
this repository (deterministic, reproducible via the helper at the bottom).
"""

from __future__ import annotations

import hashlib
import hmac

from echoquest.electrum import (
    is_old_seed,
    load_old_wordlist,
    mn_decode,
    mn_encode,
    mnemonic_to_electrum_seed,
)

OLD_WL = load_old_wordlist()


def test_old_wordlist_shape() -> None:
    assert len(OLD_WL) == 1626


def test_story_words_old_wordlist_membership() -> None:
    # VERIFIED RESEARCH FACT: the explicitly signalled dream words are NOT in
    # the legacy Electrum wordlist, so the puzzle phrase cannot be an
    # Electrum-1.x seed with those words. Lock this in as a regression.
    for w in ("maze", "fury", "renew"):
        assert w not in OLD_WL
    # ... while the pinned first word and several common words are.
    for w in ("echo", "night", "like", "upon", "more", "nothing", "strong"):
        assert w in OLD_WL


def test_old_codec_roundtrip() -> None:
    hex_seed = "0102fd0e11db6e01" * 2  # 32 hex chars -> 12 words
    words = mn_encode(hex_seed)
    assert len(words) == 12
    assert mn_decode(words) == hex_seed


def test_is_old_seed_false_for_bip39_style_words() -> None:
    phrase = "echo more vivid night like maze fury renew hint they what upon"
    assert not is_old_seed(phrase)


def test_electrum_kdf_uses_electrum_salt() -> None:
    phrase = "echo more vivid night like maze fury renew hint they what upon"
    seed = mnemonic_to_electrum_seed(phrase)
    ref = hashlib.pbkdf2_hmac("sha512", phrase.encode(), b"electrum", 2048, 64)
    assert seed == ref


def test_electrum_kdf_passphrase_changes_seed() -> None:
    phrase = "echo more vivid night like maze fury renew hint they what upon"
    assert mnemonic_to_electrum_seed(phrase) != mnemonic_to_electrum_seed(phrase, "extra")


def test_seed_version_hmac_classification() -> None:
    # deterministic Electrum-valid ("standard" tag 0x01) phrase, found by
    # search over the BIP39 wordlist (reproducible with the helper below).
    phrase = "echo silk identify echo silk identify echo silk identify echo silk army"
    d = hmac.new(b"Seed version", phrase.encode(), hashlib.sha512).digest()
    assert d[0] == 0x01


def _find_standard_tag_phrase() -> None:
    # helper used to produce the phrase above; kept for reproducibility.
    from echoquest.wordlists import load_wordlist

    wl = load_wordlist()
    base = ["echo", "silk", "identify"] * 3 + ["echo", "silk"]
    for w in wl:
        words = base + [w]
        phrase = " ".join(words)
        d = hmac.new(b"Seed version", phrase.encode(), hashlib.sha512).digest()
        if d[0] == 0x01:
            print("candidate:", phrase)  # noqa: T201
            return
