"""Low-level cryptographic and encoding helpers.

Everything here is implemented from public specifications:

* Base58 / Base58Check (Bitcoin)
* SHA-256, RIPEMD-160, HMAC-SHA512 wrappers
* secp256k1 public key derivation (via ``cryptography``)

The helpers are deliberately small and independently testable.  For the
secp256k1 group order and the known generator point we rely on the
``cryptography`` package; the tests assert well-known public vectors.
"""

from __future__ import annotations

import hashlib
import hmac
from functools import lru_cache

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# secp256k1 group order n
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {c: i for i, c in enumerate(BASE58_ALPHABET)}


def sha256(data: bytes) -> bytes:
    """SHA-256 digest."""
    return hashlib.sha256(data).digest()


def ripemd160(data: bytes) -> bytes:
    """RIPEMD-160 digest (falls back to pycryptodome if OpenSSL lacks it)."""
    try:
        return hashlib.new("ripemd160", data).digest()
    except ValueError:  # pragma: no cover - OpenSSL without legacy provider
        from Crypto.Hash import RIPEMD160

        return RIPEMD160.new(data).digest()


def sha256d(data: bytes) -> bytes:
    """Double SHA-256."""
    return sha256(sha256(data))


def hmac_sha512(key: bytes, data: bytes) -> bytes:
    """HMAC-SHA512."""
    return hmac.new(key, data, hashlib.sha512).digest()


def base58_encode(data: bytes) -> str:
    """Base58 encode with leading-zero handling."""
    x = int.from_bytes(data, "big")
    out = ""
    while x:
        x, mod = divmod(x, 58)
        out = BASE58_ALPHABET[mod] + out
    pad = len(data) - len(data.lstrip(b"\x00"))
    return "1" * pad + out


def base58_decode(text: str) -> bytes:
    """Base58 decode (raises ValueError on invalid characters)."""
    x = 0
    for c in text:
        if c not in _BASE58_INDEX:
            raise ValueError(f"invalid base58 character: {c!r}")
        x = x * 58 + _BASE58_INDEX[c]
    body = x.to_bytes((x.bit_length() + 7) // 8, "big") if x else b""
    pad = len(text) - len(text.lstrip("1"))
    return b"\x00" * pad + body


def base58check_decode(text: str) -> bytes:
    """Base58Check decode: verifies the 4-byte checksum, returns payload+version."""
    raw = base58_decode(text)
    if len(raw) < 5:
        raise ValueError("base58check data too short")
    data, checksum = raw[:-4], raw[-4:]
    if sha256d(data)[:4] != checksum:
        raise ValueError("base58check checksum mismatch")
    return data


def base58check_encode(data: bytes) -> str:
    """Base58Check encode (append 4-byte double-SHA256 checksum)."""
    return base58_encode(data + sha256d(data)[:4])


def public_key_bytes(private_key: int, compressed: bool = True) -> bytes:
    """SEC1 public key bytes for a secp256k1 private key scalar."""
    if not 1 <= private_key < SECP256K1_N:
        raise ValueError("private key scalar out of range")
    key = ec.derive_private_key(private_key, ec.SECP256K1())
    fmt = PublicFormat.CompressedPoint if compressed else PublicFormat.UncompressedPoint
    return key.public_key().public_bytes(Encoding.X962, fmt)


def p2pkh_address(private_key: int, compressed: bool = True) -> str:
    """Legacy P2PKH address (version byte 0x00) for a private key scalar."""
    h160 = ripemd160(sha256(public_key_bytes(private_key, compressed)))
    return base58check_encode(b"\x00" + h160)


def p2sh_p2wpkh_address(private_key: int) -> str:
    """P2SH-wrapped SegWit (BIP49-style) address for a private key scalar."""
    pub = public_key_bytes(private_key, True)
    redeem = b"\x00\x14" + ripemd160(sha256(pub))
    return base58check_encode(b"\x05" + ripemd160(sha256(redeem)))


def bech32_polymod(values: list[int]) -> int:
    """Bech32 checksum polymod."""
    generator = [0x3B06A32C, 0x1D8B9B6D, 0x2839DC2E, 0x01503FB8, 0x3E41D4D4]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk


BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def convertbits(data: list[int], frombits: int, tobits: int, pad: bool = True) -> list[int]:
    """General power-of-2 base conversion (BIP173 convertbits)."""
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            raise ValueError("invalid value in convertbits")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise ValueError("invalid padding in convertbits")
    return ret


def p2wpkh_address(private_key: int) -> str:
    """Native SegWit v0 P2WPKH bech32 address (BIP84 style) for a scalar key."""
    h160 = ripemd160(sha256(public_key_bytes(private_key, True)))
    data = convertbits(list(h160), 8, 5)
    values = _bech32_expand("bc") + [0] + data
    polymod = bech32_polymod(values) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return "bc1q" + "".join(BECH32_CHARSET[d] for d in data + checksum)


@lru_cache(maxsize=None)
def word_digest_cached(text: str) -> str:
    """SHA-256 hex digest of an exact string (used for redacted proofs)."""
    return sha256(text.encode("utf-8")).hexdigest()
