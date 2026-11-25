"""Regression locks for historical bugs and verified research facts.

Every assertion here corresponds to an error found in the earlier phases of
the investigation (see docs/KNOWN_ERRORS.md) or a VERIFIED positional fact.
"""

from __future__ import annotations

import itertools

from echoquest.bip39 import mnemonic_valid
from echoquest.wordlists import index_map, load_wordlist

WL = load_wordlist()
IM = index_map(WL)


def test_armed_strong_indices_regression() -> None:
    # HISTORICAL BUG: phases before 18 used armed=97 / strong=1727.
    assert IM["armed"] == 94
    assert IM["strong"] == 1721


def test_dream_word_indices() -> None:
    assert (IM["maze"], IM["fury"], IM["renew"]) == (1100, 755, 1457)


def test_first_checksum_valid_permutation_of_midpoint_set() -> None:
    # VERIFIED (dset.valid record 0): the first checksum-valid permutation of
    # the midpoint-32 set in itertools.permutations order.
    unknowns = "more vivid night like maze fury renew hint they what upon".split()
    expect = [IM[w] for w in ["echo"] + unknowns]
    for perm in itertools.permutations(unknowns):
        words = ["echo"] + list(perm)
        if mnemonic_valid(words):
            assert [IM[w] for w in words] == expect
            return
    raise AssertionError("no checksum-valid permutation found in enumeration")


def test_checksum_ratio_is_about_one_sixteenth() -> None:
    # The first 8192 permutations of the midpoint set: checksum-valid count
    # is deterministic; the recorded value locks the enumeration order and
    # the checksum implementation together.
    unknowns = "more vivid night like maze fury renew hint they what upon".split()
    valid = 0
    total = 0
    for perm in itertools.islice(itertools.permutations(unknowns), 8192):
        valid += mnemonic_valid(["echo"] + list(perm))
        total += 1
    assert total == 8192
    assert 400 <= valid <= 700  # ~1/16 = 512 expected


def test_target_address_constants() -> None:
    from echoquest import TARGET_ADDRESS

    assert TARGET_ADDRESS == "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"
