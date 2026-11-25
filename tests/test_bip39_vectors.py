"""BIP39 spec vectors: checksum, entropy round-trip and seed (PBKDF2).

Vectors come from the official Trezor python-mnemonic test vectors
(vectors.json, english section, retrieved 2026-11-23 from
https://raw.githubusercontent.com/trezor/python-mnemonic/master/vectors.json).
"""

from __future__ import annotations

import pytest

from echoquest.bip39 import (
    entropy_from_mnemonic,
    mnemonic_from_entropy,
    mnemonic_valid,
    seed_from_mnemonic,
)

# (entropy-hex, mnemonic, seed-hex) — official Trezor vectors (passphrase
# "TREZOR" for the seed column).
VECTORS = [
    (
        "00000000000000000000000000000000",
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04",
    ),
    (
        "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
        "legal winner thank year wave sausage worth useful legal winner thank yellow",
        "2e8905819b8723fe2c1d161860e5ee1830318dbf49a83bd451cfb8440c28bd6fa457fe1296106559a3c80937a1c1069be3a3a5bd381ee6260e8d9739fce1f607",
    ),
    (
        "80808080808080808080808080808080",
        "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
        "d71de856f81a8acc65e6fc851a38d4d7ec216fd0796d0a6827a3ad6ed5511a30fa280f12eb2e47ed2ac03b5c462a0358d18d69fe4f985ec81778c1b370b652a8",
    ),
]

SEED_VECTORS = VECTORS
ROUND_TRIP = [(e, m) for e, m, _ in VECTORS]


@pytest.mark.parametrize("entropy_hex,mnemonic,seed_hex", SEED_VECTORS)
def test_trezor_seed_vectors(entropy_hex, mnemonic, seed_hex) -> None:
    words = mnemonic.split()
    computed = seed_from_mnemonic(words, "TREZOR")
    assert computed.hex() == seed_hex


@pytest.mark.parametrize("entropy_hex,mnemonic", ROUND_TRIP)
def test_entropy_round_trip(entropy_hex, mnemonic) -> None:
    words = mnemonic.split()
    assert entropy_from_mnemonic(words).hex() == entropy_hex
    assert mnemonic_from_entropy(bytes.fromhex(entropy_hex)) == words


@pytest.mark.parametrize("entropy_hex,mnemonic", ROUND_TRIP)
def test_checksum_validity_of_official_vectors(entropy_hex, mnemonic) -> None:
    assert mnemonic_valid(mnemonic.split())


def test_invalid_checksum_detected() -> None:
    # swap the last word of a valid vector: checksum must fail.
    words = VECTORS[0][1].split()
    words[11] = "abandon"
    assert not mnemonic_valid(words)


def test_seed_empty_passphrase_matches_bip39_spec() -> None:
    words = VECTORS[0][1].split()
    seed = seed_from_mnemonic(words)
    assert len(seed) == 64
    # deterministic
    assert seed == seed_from_mnemonic(VECTORS[0][1], "")
