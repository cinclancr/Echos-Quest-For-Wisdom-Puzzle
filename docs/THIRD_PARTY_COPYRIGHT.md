# Third-party copyright details

## Story, video, X post
Author/publisher: the puzzle author (IMineBlocks). Not redistributed here;
analysis of a legally obtained copy. Fair-use style quotation is limited to
short attributed factual statements (titles, the one-line hint) in
README/docs.

## BIP39 English wordlist (data/english.txt)
From the bitcoin/bips repository (bip-0039/english.txt). The wordlists are
placed in the public domain by their author (Marc Alexander, "unlicence"
statement in the BIP39 appendix). Redistribution is unmodified, with the
SHA-256 pinned and verified at load.

## Electrum legacy wordlist (data/electrum_old_wordlist.txt)
From the spesmilo/electrum repository (electrum/old_wordlist). Electrum is
MIT-licensed; the file is redistributed unmodified with this notice. Used
for read-only seed-format compatibility checks.

## Trezor test vectors
Three entries from python-mnemonic's vectors.json are embedded in
tests/test_bip39_vectors.py with attribution; the project is MIT-licensed
and the vector file is MIT-licensed upstream (see
https://github.com/trezor/python-mnemonic/blob/master/LICENSE).

## BIP32 test vector
Test vector 1 from BIP-0032 (public domain specification text) is embedded
in tests/test_bip32_bip44.py.

## Libraries
* `cryptography` (Apache-2.0 OR BSD-3-Clause)
* OpenSSL / libcrypto (Apache-2.0)
Both used via their public APIs only.
