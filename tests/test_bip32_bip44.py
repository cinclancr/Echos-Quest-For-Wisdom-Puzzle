"""BIP32/BIP44: official spec vectors and derivation paths."""

from __future__ import annotations

import struct

from echoquest.bip39 import seed_from_mnemonic
from echoquest.utils import base58check_encode
from echoquest.wallet import ckd_priv, derive_priv, master_key, parse_path


def _xprv(key: int, chain: bytes, depth: int, fingerprint: bytes, idx: int) -> str:
    data = (
        b"\x04\x88\xad\xe4"
        + bytes([depth])
        + fingerprint
        + struct.pack(">I", idx)
        + chain
        + b"\x00"
        + key.to_bytes(32, "big")
    )
    return base58check_encode(data)


def test_bip32_vector_1_master() -> None:
    # BIP32 spec test vector 1: seed 000102...0e0f
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    m = master_key(seed)
    assert _xprv(m.key, m.chain, 0, b"\x00" * 4, 0) == (
        "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi"
    )


def test_bip32_vector_1_children() -> None:
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    m = master_key(seed)
    c0 = ckd_priv(m, 0x80000000)  # m/0'
    assert _xprv(c0.key, c0.chain, 1, m.fingerprint(), 0x80000000) == (
        "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7"
    )
    c01 = ckd_priv(c0, 1)  # m/0'/1
    assert _xprv(c01.key, c01.chain, 2, c0.fingerprint(), 1) == (
        "xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"
    )
    c012 = ckd_priv(c01, 0x80000002)  # m/0'/1/2'
    assert _xprv(c012.key, c012.chain, 3, c01.fingerprint(), 0x80000002) == (
        "xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM"
    )


def test_parse_path_roundtrip() -> None:
    assert parse_path("m/44'/0'/0'/0/0") == [0x8000002C, 0x80000000, 0x80000000, 0, 0]
    assert parse_path("m") == []
    assert parse_path("m/0/0") == [0, 0]


def test_derive_priv_matches_stepwise() -> None:
    seed = seed_from_mnemonic("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about")
    k_path = derive_priv(seed, "m/44'/0'/0'/0/0")
    node = master_key(seed)
    for idx in parse_path("m/44'/0'/0'/0/0"):
        node = ckd_priv(node, idx)
    assert k_path == node.key


def test_invalid_path_raises() -> None:
    import pytest

    from echoquest.wallet import DerivationError

    with pytest.raises(DerivationError):
        parse_path("44'/0'/0'/0/0")
    with pytest.raises(DerivationError):
        parse_path("m/notanumber/0")
