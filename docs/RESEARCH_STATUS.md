# Research status

_Last updated: 2026-11-25 (UTC)._

**Puzzle status: UNSOLVED.** No mnemonic has been verified against the target
address `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx`. This page tracks what is
VERIFIED, what was tried with exact coverage, and what is next.

## VERIFIED facts

1. **Story provenance** — the byte-exact research copy hashes (SHA-256, UTF-8,
   LF) to `437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0`.
2. **Tokenisation** — dCode-style rule (`[A-Za-z0-9]+`, case-folded,
   apostrophes split, title included): **512 tokens**, 11 paragraphs incl.
   title, 32 narrative sentences. Apostrophe-preserving rule: **509 tokens**.
3. **Anchor positions (1-based, dCode rule)** — `echo`:
   [1, 74, 154, 173, 226, 257, 300, 342, 376, 412, 444]; `grace`: 10
   narrative occurrences; `shade`: [14, 494]; `cryptic`: [249, 274];
   `maze/fury/renew`: 268/269/271.
4. **Midpoint row** — tokens 257–288 start at the second `Echo's` and contain
   **12 distinct BIP39 words** including `echo` and all three dream words
   (`echo more vivid night like maze fury renew hint what they upon`).
5. **Paragraph-5 singletons** — 12 BIP39 words occurring exactly once in the
   story: `next morning armed nothing strong more vivid night maze fury
   renew hint` (+ `echo` = 13; one word must drop for a 12-word phrase).
6. **Wordlist indices (independently audited)** — `echo=559`, `maze=1100`,
   `fury=755`, `renew=1457`, `armed=94`, `strong=1721` (the last two fix the
   historical mis-entry 97/1727).
7. **Target address structure** — `1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx` decodes
   to version `0x00` (P2PKH), hash160 `a6467f506442ff5766bd313515901d9292c84e53`.
8. **Electrum legacy wordlist membership** — `maze`, `fury`, `renew` are NOT
   in the 1626-word legacy list ⇒ the puzzle phrase cannot be an Electrum 1.x
   seed.

## Phase results (2026-11-24/25): the no-checksum turn

Motivated by the maintainer's insight that the twelve words need NOT form a
checksum-valid mnemonic (PBKDF2 works on any words), this phase removed every
checksum gate:

| Experiment | Coverage | Result |
|---|---|---|
| Natural-order battery (21 candidate sets × ~4-6 story orders × 12 passphrases × 2 KDFs × 15 paths × 2 encodings) | 61,200 comparisons | **0 matches** |
| Brainwallet-style (SHA256 of the phrase as private key, 4 string forms × both encodings × 21 sets) | 168 comparisons | **0 matches** |
| Electrum-standard-tag permutation scan, midpoint-32 set (all 11! arrangements; Electrum-version filter, m/0/0) | 39,916,800 perms, ~155K derived | **0 matches** |
| Electrum-standard-tag permutation scan, p5-no-next set | 39,916,800 perms | **0 matches** |
| Electrum-standard-tag permutation scan, p5-no-hint set | 39,916,800 perms | **0 matches** |
| Full no-checksum permutation scan of midpoint-32 set (BIP39 KDF, `m/44'/0'/0'/0/0`, both encodings) | see `results/scan/ncs.state.b*` for the exact, dated checkpoint | in progress |
| Checksum-gated scan (previous phase, same set) | 1,391,882 of 2,492,947 checksum-valid perms at the primary path | 0 matches |

Cross-validation: the C scanner's checksum-valid count over the complete
midpoint set is **2,492,947**, exactly matching the earlier independent Python
enumeration; the scanner's hand-written Montgomery secp256k1 core matches
OpenSSL on 1000+ differential scalars; BIP39/BIP32 outputs match the official
Trezor and BIP-0032 test vectors.

## Current hypothesis ranking

1. **Midpoint-32 row words in an unknown order, BIP39 KDF, primary path,
   checksum-invalid** — the running full scan targets exactly this.
2. **Same sets under alternative wallet formats** (custom derivation path,
   passphrase, Electrum with non-zero address index) — partially excluded
   (see table above), partially open.
3. **A different word set entirely** — the extraction rule is still unknown;
   the catalogue in `results/extractions.csv` lists every rule tested.

## Open questions

* The author's exact extraction rule (word selection + ordering) — the core
  unsolved problem. The story must define it without external hints.
* The wallet format/derivation used for the address (P2PKH, address index 0
  assumed; BIP44-vs-Electrum-vs-custom unknown).
* Whether the phrase carries a BIP39 passphrase.

## See also

* [HYPOTHESES.md](HYPOTHESES.md) — the ledger of every extraction rule family.
* [RESULTS.md](RESULTS.md) — raw experiment outcomes with exact coverage.
* [KNOWN_ERRORS.md](KNOWN_ERRORS.md) — historical mistakes and their fixes.
* [HOW_TO_REPRODUCE.md](HOW_TO_REPRODUCE.md) — command-by-command reproduction.
* [SOLUTION.md](SOLUTION.md) — why nothing is claimed as solved.
