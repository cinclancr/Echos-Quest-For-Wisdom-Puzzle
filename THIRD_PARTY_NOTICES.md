# Third-party notices

This project's own code and documentation are licensed under the MIT licence
(LICENSE). The materials listed below are **not** covered by that licence and
are owned/licensed by their respective rights holders. Where a file is
redistributed here, its terms permit that redistribution; otherwise only
references, hashes and acquisition instructions are provided.

## Puzzle source material (NOT redistributed)

* The story "Echo's Quest For Wisdom" (the puzzle ciphertext). Rights holder:
  the puzzle author (IMineBlocks). **Not committed to this repository.**
  Provenance: author's video description (URL and date in
  `data/source_provenance.json` and README). Local research copies live
  under the git-ignored `private/` directory. Researchers must obtain the
  text from the author's published sources. Research SHA-256 (UTF-8, LF
  newlines): `437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0`.
* The video `https://www.youtube.com/watch?v=k5WIlZcXJHI` and its transcript.
  Quoted only for short, attributed factual statements (duration, title).
* The X post `https://x.com/IMineBlocks_com/status/1894292681397829677` and
  the user-relayed author quote "I leaked my #Bitcoin seed phrase in plain
  text and after one year the wallet is still safe. How?" — quoted with
  attribution and provenance caveats (user-supplied, not independently
  re-verified).

Text analysis of a legally obtained copy (tokenisation, counting, hypothesis
testing) is the whole point of this repository and is conducted read-only.

## Redistributed data files

* `data/english.txt` — the official BIP39 English wordlist from the
  bitcoin/bips repository (`bip-0039/english.txt`), unmodified.
  Upstream: <https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt>
  SHA-256: `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`.
  The BIP-0039 wordlists are placed in the public domain (unlicence) by
  their author (Marc Alexander); redistribution is permitted. The file is
  integrity-checked at load time by `echoquest.wordlists`.
* `data/electrum_old_wordlist.txt` — the Electrum legacy 1626-word seed
  wordlist from the spesmilo/electrum repository
  (`electrum/old_wordlist`). Upstream:
  <https://raw.githubusercontent.com/spesmilo/electrum/master/electrum/old_wordlist>.
  Used for read-only compatibility checks (Electrum v1 seed decoding).
  The Electrum project is MIT-licensed; see
  [docs/THIRD_PARTY_COPYRIGHT.md](docs/THIRD_PARTY_COPYRIGHT.md).

## Libraries used

* `cryptography` (Python) — used for secp256k1 point operations.
  Apache-2.0 OR BSD-3-Clause, © The cryptography developers.
* OpenSSL (libcrypto) — the C scanner uses its SHA-2/RIPEMD-160/HMAC/PBKDF2
  and (for cross-validation) EC implementations. Apache-2.0,
  © The OpenSSL Project Authors.
* The hand-written Montgomery secp256k1 core in
  `scripts/experiments/nochecksum_scan.c` is original code for this project
  (MIT, as the rest of the repository) and is validated against OpenSSL at
  every `selftest` run.

## Trademarks

"Bitcoin", "Electrum" and product names are used descriptively; no
affiliation or endorsement is implied.
