# Sources

## Primary puzzle sources (owned by the puzzle author)

| Source | URL | Notes |
|---|---|---|
| YouTube video | https://www.youtube.com/watch?v=k5WIlZcXJHI | title "A Bitcoin Puzzle - Echo's Quest For Wisdom", duration 305 s (per user-supplied metadata JSON) |
| Channel ID | `UCjYHcWGAjUVqU49D2JOKD3w` | |
| X post | https://x.com/IMineBlocks_com/status/1894292681397829677 | replies/assets not reliably accessed during research |
| Story text | author's video description | NOT redistributed; research copy under git-ignored `private/`; SHA-256 `437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0` |
| Puzzle address | `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx` | read-only comparison target |
| Announced hint | "The first word is echo, the next 11 words can be found within the story text." | from the video description |
| Author quote (user-relayed) | "I leaked my #Bitcoin seed phrase in plain text and after one year the wallet is still safe. How?" | provenance: user relay; not independently re-verified |

## Standards and specifications

* BIP39 — https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
  (wordlist: `bip-0039/english.txt`, SHA-256
  `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`)
* BIP32 — https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
  (test vector 1 used in tests)
* BIP44 — https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki
* BIP173 (bech32) — used for the P2WPKH helper
* Electrum source — https://github.com/spesmilo/electrum (seed version
  check, `mnemonic_to_seed` salt `electrum`, legacy 1626-word list and
  `mn_decode`; verified 2026-11-23 from the master branch)

## Test vectors

* Trezor python-mnemonic vectors —
  https://raw.githubusercontent.com/trezor/python-mnemonic/master/vectors.json
  (retrieved 2026-11-23; three English entries embedded in
  tests/test_bip39_vectors.py)

## Prior research artefacts

* The context bundle `Echo_GLM53_Research_Context.zip` (phases 0–18
  experiments) supplied by the maintainer; its claims were re-audited
  before being relied upon (see KNOWN_ERRORS.md and PRIOR_EXPERIMENTS.md).
