"""Read-only BIP32/BIP44 key derivation and legacy address encoding.

Implements:

* BIP32 master key: HMAC-SHA512("Bitcoin seed", seed) -> (k, chain)
* BIP32 CKDpriv for hardened and normal derivation
* BIP44-style path parsing (``m/44'/0'/0'/0/0``)
* P2PKH (version 0x00), P2SH-P2WPKH (0x05) and P2WPKH (bech32) encodings

No signing, no transaction construction, no network access.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass

from .utils import SECP256K1_N, hmac_sha512, p2pkh_address, p2sh_p2wpkh_address, p2wpkh_address, public_key_bytes

_PATH_STEP = re.compile(r"^(\d+)(['hH])?$")

STANDARD_PATHS = {
    "bip44": "m/44'/0'/0'/0/0",
    "bip49": "m/49'/0'/0'/0/0",
    "bip84": "m/84'/0'/0'/0/0",
    "bip32-root": "m",
    "electrum-bip44": "m/44'/0'/0'/0/0",
}


class DerivationError(ValueError):
    """Raised for invalid paths or invalid child keys."""


@dataclass(frozen=True)
class ExtendedPriv:
    """A BIP32 private key node (secret scalar + chain code)."""

    key: int
    chain: bytes
    depth: int = 0
    parent_fingerprint: bytes = b"\x00\x00\x00\x00"
    index: int = 0

    def fingerprint(self) -> bytes:
        from .utils import ripemd160, sha256

        return ripemd160(sha256(public_key_bytes(self.key)))[:4]


def master_key(seed: bytes) -> ExtendedPriv:
    """BIP32 master private key from a seed blob."""
    digest = hmac_sha512(b"Bitcoin seed", seed)
    key = int.from_bytes(digest[:32], "big")
    if not 0 < key < SECP256K1_N:
        raise DerivationError("invalid master key (out of secp256k1 range)")
    return ExtendedPriv(key=key, chain=digest[32:])


def ckd_priv(parent: ExtendedPriv, index: int) -> ExtendedPriv:
    """BIP32 CKDpriv (hardened when index >= 2**31)."""
    if not 0 <= index < 2**32:
        raise DerivationError("child index out of range")
    if index >= 0x80000000:
        data = b"\x00" + parent.key.to_bytes(32, "big") + struct.pack(">I", index)
    else:
        data = public_key_bytes(parent.key, True) + struct.pack(">I", index)
    digest = hmac_sha512(parent.chain, data)
    tweak = int.from_bytes(digest[:32], "big")
    child = (tweak + parent.key) % SECP256K1_N
    if tweak >= SECP256K1_N or child == 0:
        raise DerivationError("invalid child key (skip this index)")
    return ExtendedPriv(
        key=child,
        chain=digest[32:],
        depth=parent.depth + 1,
        parent_fingerprint=parent.fingerprint(),
        index=index,
    )


def parse_path(path: str) -> list[int]:
    """Parse a BIP32 path string like ``m/44'/0'/0'/0/0`` into indices."""
    path = path.strip()
    if path in ("m", "", "M"):
        return []
    if not path[0] in "mM" or path[1] != "/":
        raise DerivationError(f"invalid path: {path!r}")
    out: list[int] = []
    for step in path[2:].split("/"):
        m = _PATH_STEP.match(step)
        if not m:
            raise DerivationError(f"invalid path step: {step!r}")
        idx = int(m.group(1))
        if idx >= 2**31:
            raise DerivationError(f"index too large: {step!r}")
        out.append(idx + 0x80000000 if m.group(2) else idx)
    return out


def derive_priv(seed: bytes, path: str) -> int:
    """Private key scalar at ``path`` for a BIP39-style seed."""
    node = master_key(seed)
    for idx in parse_path(path):
        node = ckd_priv(node, idx)
    return node.key


def address_for(seed: bytes, path: str, address_type: str = "p2pkh", compressed: bool = True) -> str:
    """Derive an address for a seed and path.

    ``address_type``: ``p2pkh`` (legacy, may be compressed or uncompressed),
    ``p2sh-p2wpkh`` (BIP49-style) or ``p2wpkh`` (BIP84-style).
    """
    k = derive_priv(seed, path)
    if address_type == "p2pkh":
        return p2pkh_address(k, compressed)
    if address_type == "p2sh-p2wpkh":
        return p2sh_p2wpkh_address(k)
    if address_type == "p2wpkh":
        return p2wpkh_address(k)
    raise ValueError(f"unknown address type: {address_type}")
