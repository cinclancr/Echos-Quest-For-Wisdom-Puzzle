"""Address encoding: base58check, the puzzle target, and golden addresses."""

from __future__ import annotations

import pytest

from echoquest.bip39 import seed_from_mnemonic
from echoquest.utils import (
    base58_decode,
    base58check_decode,
    base58check_encode,
    p2pkh_address,
)
from echoquest.wallet import address_for, derive_priv

TARGET = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"


def test_base58check_roundtrip() -> None:
    payload = b"\x00" + b"\x11" * 20
    enc = base58check_encode(payload)
    assert base58check_decode(enc) == payload


def test_target_address_decodes_to_p2pkh_version() -> None:
    raw = base58check_decode(TARGET)
    assert raw[0] == 0x00
    assert len(raw) == 21
    assert raw[1:].hex() == "a6467f506442ff5766bd313515901d9292c84e53"


def test_base58_invalid_char_raises() -> None:
    with pytest.raises(ValueError):
        base58_decode("0OIl")


def test_base58_leading_zeros() -> None:
    assert base58_decode("111") == b"\x00\x00\x00"


def test_golden_address_abandon_about_primary_path() -> None:
    seed = seed_from_mnemonic(
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    )
    assert address_for(seed, "m/44'/0'/0'/0/0", "p2pkh", True) == "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"
    assert address_for(seed, "m/44'/0'/0'/0/0", "p2pkh", False) == "18LhnLKXjcTw5xJFiTxntnKit2Gd63eWFm"


def test_compressed_and_uncompressed_differ() -> None:
    seed = seed_from_mnemonic(
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    )
    k = derive_priv(seed, "m/0/0")
    assert p2pkh_address(k, True) != p2pkh_address(k, False)


def test_address_is_deterministic() -> None:
    seed = seed_from_mnemonic(
        "legal winner thank year wave sausage worth useful legal winner thank yellow"
    )
    a1 = address_for(seed, "m/44'/0'/0'/0/0")
    a2 = address_for(seed, "m/44'/0'/0'/0/0")
    assert a1 == a2 and a1.startswith("1")
