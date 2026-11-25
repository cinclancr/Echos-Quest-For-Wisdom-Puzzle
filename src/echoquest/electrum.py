"""Electrum seed format support (read-only derivation checks).

Implements the algorithms used by Electrum (spesmilo/electrum), verified
against the upstream source (master branch, retrieved 2026-11-23):

* **New seeds** (Electrum 2.x+): the seed type is decided by
  ``HMAC-SHA512(b"Seed version", NFKD(mnemonic)).hex()`` starting with
  ``01`` (standard), ``100`` (segwit), ``101`` (2FA) or ``102`` (2FA
  segwit).  The binary seed is
  ``PBKDF2-HMAC-SHA512(NFKD(mnemonic), b'electrum'+NFKD(passphrase), 2048, 64)``
  (note: salt prefix is ``electrum``, NOT the BIP39 ``mnemonic``).
  Standard wallets then derive BIP32 from "Bitcoin seed" at ``m/`` (the
  root) and produce P2PKH addresses at ``m/0/i`` (receiving) and
  ``m/1/i`` (change).  Segwit wallets derive at ``m/0'/`` and produce
  P2WPKH addresses at ``m/0'/i``.

* **Old seeds** (Electrum 1.x): 12 words from the 1626-word legacy
  wordlist (bundled as ``data/electrum_old_wordlist.txt``), decoded by
  the ``mn_decode`` carry chain into 16 hex bytes; the master secret is
  stretched with 100000 rounds of ``sha256(x + hex_seed)``; child keys
  are ``secexp + sha256d(b"{n}:{c}:{mpk}")`` mod n and addresses are
  P2PKH with UNCOMPRESSED public keys.

This module never writes wallet files and never signs anything.
"""

from __future__ import annotations

import hashlib
import hmac
import unicodedata
from pathlib import Path

from .utils import (
    SECP256K1_N,
    p2pkh_address,
    sha256d,
)

OLD_WORDLIST_PATH = Path(__file__).resolve().parents[2] / "data" / "electrum_old_wordlist.txt"

SEED_PREFIX_STANDARD = "01"
SEED_PREFIX_SW = "100"
SEED_PREFIX_2FA = "101"
SEED_PREFIX_2FA_SW = "102"


def _normalize(text: str) -> str:
    """Electrum text normalisation (NFKD, collapse whitespace)."""
    text = unicodedata.normalize("NFKD", text)
    text = " ".join(text.split())
    return text


def load_old_wordlist(path: str | Path | None = None) -> list[str]:
    """Load the 1626-word legacy Electrum wordlist."""
    p = Path(path) if path is not None else OLD_WORDLIST_PATH
    words = p.read_text("utf-8").split()
    if len(words) != 1626 or len(set(words)) != 1626:
        raise ValueError("legacy Electrum wordlist must contain 1626 unique words")
    return words


def electrum_seed_type(mnemonic: str) -> str | None:
    """Classify an Electrum mnemonic: 'standard', 'segwit', '2fa', '2fa_segwit', 'old', or None."""
    x = _normalize(mnemonic)
    num_words = len(x.split())
    if is_old_seed(x):
        return "old"
    if hmac_new_seed(x, SEED_PREFIX_STANDARD):
        return "standard"
    if hmac_new_seed(x, SEED_PREFIX_SW):
        return "segwit"
    if hmac_new_seed(x, SEED_PREFIX_2FA) and (num_words == 12 or num_words >= 20):
        return "2fa"
    if hmac_new_seed(x, SEED_PREFIX_2FA_SW):
        return "2fa_segwit"
    return None


def hmac_new_seed(normalized_mnemonic: str, prefix: str) -> bool:
    digest = hmac.new(b"Seed version", normalized_mnemonic.encode("utf-8"), hashlib.sha512).hexdigest()
    return digest.startswith(prefix)


def is_old_seed(seed: str) -> bool:
    """True for 12/24-word legacy seeds decodable via the old wordlist (or 16/32 byte hex)."""
    x = _normalize(seed)
    words = x.split()
    if len(words) not in (12, 24):
        return False
    old = load_old_wordlist()
    try:
        mn_decode(words, old)
        return True
    except ValueError:
        return False


# --- old seed codec ------------------------------------------------------------


def mn_decode(words: list[str], wordlist: list[str] | None = None) -> str:
    """Legacy Electrum word-group decoder: 3 words -> 8 hex chars."""
    wl = wordlist if wordlist is not None else load_old_wordlist()
    n = len(wl)
    out = ""
    for i in range(len(words) // 3):
        w1, w2, w3 = words[3 * i : 3 * i + 3]
        try:
            i1, i2, i3 = wl.index(w1), wl.index(w2), wl.index(w3)
        except ValueError as exc:
            raise ValueError(f"word not in legacy wordlist: {exc}") from exc
        x = i1 + n * ((i2 - i1) % n) + n * n * ((i3 - i2) % n)
        out += f"{x:08x}"
    return out


def mn_encode(hex_message: str, wordlist: list[str] | None = None) -> list[str]:
    """Legacy Electrum encoder: 8 hex chars -> 3 words."""
    wl = wordlist if wordlist is not None else load_old_wordlist()
    n = len(wl)
    out: list[str] = []
    for i in range(len(hex_message) // 8):
        chunk = hex_message[8 * i : 8 * i + 8]
        x = int(chunk, 16)
        w1 = x % n
        w2 = ((x // n) + w1) % n
        w3 = ((x // n // n) + w2) % n
        out += [wl[w1], wl[w2], wl[w3]]
    return out


# --- old seed key derivation ---------------------------------------------------


def stretch_key(hex_seed: str) -> int:
    """Legacy stretch: 100000 rounds of sha256(x + hex_seed_ascii)."""
    encoded = hex_seed.encode("ascii")
    x = encoded
    for _ in range(100000):
        x = hashlib.sha256(x + encoded).digest()
    return int.from_bytes(x, "big")


def old_master_public_key(hex_seed: str) -> str:
    """Legacy master public key (uncompressed pubkey hex without 04 prefix)."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    secexp = stretch_key(hex_seed)
    key = ec.derive_private_key(secexp % SECP256K1_N, ec.SECP256K1())
    raw = key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return raw[2:].hex()


def old_sequence(mpk_hex: str, for_change: int, n: int) -> int:
    return int.from_bytes(sha256d(f"{n}:{for_change}:".encode("ascii") + bytes.fromhex(mpk_hex)), "big")


def old_private_key(hex_seed: str, for_change: int, n: int) -> int:
    """Legacy child private key for address (n, for_change)."""
    secexp = stretch_key(hex_seed)
    mpk = old_master_public_key(hex_seed)
    z = old_sequence(mpk, for_change, n)
    return (secexp + z) % SECP256K1_N


def old_address(hex_seed: str, for_change: int, n: int) -> str:
    """Legacy Electrum P2PKH address (uncompressed key)."""
    return p2pkh_address(old_private_key(hex_seed, for_change, n), compressed=False)


# --- new seed derivation -------------------------------------------------------


def mnemonic_to_electrum_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Electrum 2.x binary seed: PBKDF2 with the ``electrum`` salt prefix."""
    m = _normalize(mnemonic)
    p = _normalize(passphrase) if passphrase else ""
    return hashlib.pbkdf2_hmac("sha512", m.encode("utf-8"), b"electrum" + p.encode("utf-8"), 2048, 64)


def electrum_standard_addresses(mnemonic: str, passphrase: str = "", count: int = 20, change_count: int = 5) -> list[str]:
    """Legacy P2PKH addresses for a new-style standard Electrum seed.

    Standard wallets derive the keystore at ``m/`` (BIP32 root) and take
    receiving addresses at ``m/0/i`` and change at ``m/1/i``.
    """
    from .wallet import derive_priv

    seed = mnemonic_to_electrum_seed(mnemonic, passphrase)
    addrs: list[str] = []
    for i in range(count):
        addrs.append(p2pkh_address(derive_priv(seed, f"m/0/{i}"), True))
    for i in range(change_count):
        addrs.append(p2pkh_address(derive_priv(seed, f"m/1/{i}"), True))
    return addrs


def electrum_segwit_addresses(mnemonic: str, passphrase: str = "", count: int = 20) -> list[str]:
    """P2WPKH bech32 addresses for a new-style segwit Electrum seed (m/0'/i)."""
    from .utils import p2wpkh_address
    from .wallet import derive_priv

    seed = mnemonic_to_electrum_seed(mnemonic, passphrase)
    return [p2wpkh_address(derive_priv(seed, f"m/0'/{i}")) for i in range(count)]
