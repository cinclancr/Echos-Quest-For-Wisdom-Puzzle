"""Spec-conformant BIP39 checksum and seed computation.

Implements the BIP39 reference algorithm for English mnemonics:

* 12 words = 128 entropy bits + 4 checksum bits (SHA-256 first byte >> 4)
* word index -> 11-bit big-endian chunks
* seed = PBKDF2-HMAC-SHA512(NFKD(mnemonic), "mnemonic" + NFKD(passphrase), 2048, 64)

The test suite validates against the official BIP39 test vectors.
"""

from __future__ import annotations

import hashlib
import unicodedata

from .wordlists import load_wordlist

PBKDF2_ROUNDS = 2048
SEED_LENGTH = 64


def word_indices(words: list[str], wordlist: list[str] | None = None) -> list[int]:
    """Map mnemonic words to 0-based indices (KeyError on unknown word)."""
    wl = wordlist if wordlist is not None else load_wordlist()
    index = {w: i for i, w in enumerate(wl)}
    return [index[w] for w in words]


def indices_to_bits(indices: list[int]) -> str:
    """Concatenate 11-bit big-endian index chunks."""
    return "".join(f"{i:011b}" for i in indices)


def checksum_bits(entropy: bytes) -> str:
    """Checksum bits for an entropy blob (len(entropy)*8/32 bits)."""
    n_bits = len(entropy) * 8 // 32
    digest = hashlib.sha256(entropy).digest()
    full = int.from_bytes(digest, "big")
    return format(full >> (256 - n_bits), f"0{n_bits}b")


def mnemonic_valid(words: list[str], wordlist: list[str] | None = None) -> bool:
    """True when the mnemonic has valid length, membership and checksum."""
    if len(words) not in (12, 15, 18, 21, 24):
        return False
    try:
        indices = word_indices(words, wordlist)
    except KeyError:
        return False
    bits = indices_to_bits(indices)
    total = len(bits)
    ent_bits = total * 32 // 33
    cs_bits = total - ent_bits
    entropy = int(bits[:ent_bits], 2).to_bytes(ent_bits // 8, "big")
    expected = checksum_bits(entropy)
    return bits[ent_bits:] == expected[:cs_bits]


def entropy_from_mnemonic(words: list[str], wordlist: list[str] | None = None) -> bytes:
    """Recover the entropy bytes of a valid mnemonic (raises ValueError)."""
    if not mnemonic_valid(words, wordlist):
        raise ValueError("mnemonic is not BIP39-valid")
    indices = word_indices(words, wordlist)
    bits = indices_to_bits(indices)
    ent_bits = len(bits) * 32 // 33
    return int(bits[:ent_bits], 2).to_bytes(ent_bits // 8, "big")


def mnemonic_from_entropy(entropy: bytes, wordlist: list[str] | None = None) -> list[str]:
    """Build the (checksum-valid) mnemonic for an entropy blob."""
    wl = wordlist if wordlist is not None else load_wordlist()
    if len(entropy) * 8 % 32 != 0:
        raise ValueError("entropy length must be a multiple of 32 bits")
    cs_bits = len(entropy) * 8 // 32
    bits = format(int.from_bytes(entropy, "big"), f"0{len(entropy) * 8}b") + checksum_bits(entropy)[:cs_bits]
    indices = [int(bits[i : i + 11], 2) for i in range(0, len(bits), 11)]
    return [wl[i] for i in indices]


def seed_from_mnemonic(words: list[str] | str, passphrase: str = "") -> bytes:
    """BIP39 seed: PBKDF2-HMAC-SHA512 over NFKD-normalised text.

    Accepts either a list of words or a whitespace-separated string.
    """
    if isinstance(words, str):
        words = words.split()
    mnemonic = unicodedata.normalize("NFKD", " ".join(words))
    salt = "mnemonic" + unicodedata.normalize("NFKD", passphrase)
    return hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ROUNDS, SEED_LENGTH)
