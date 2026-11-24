# Solution — status page

**UNSOLVED.** As of 2026-11-25 no twelve-word phrase for the address
`1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx` has been demonstrated.

## What would count as "solved"

A specific, story-grounded extraction rule R such that:

1. applying R to the byte-exact story yields twelve BIP39 words (first word
   `echo`),
2. deriving the wallet from those words under a stated format (KDF, path,
   encoding, passphrase) reproduces the target address bit-for-bit,
3. the reproduction is independent (two implementations, two wordlist
   copies) — the C scanner and the Python toolkit here satisfy this need.

## Why the current strongest candidates are not "solved"

* Midpoint-32 set (`echo more vivid night like maze fury renew hint what
  they upon`): natural orders fail under every tested KDF/path/passphrase/
  encoding; all Electrum-standard permutations fail at m/0/0; the full
  no-checksum BIP39 scan is in progress (see RESEARCH_STATUS.md for the
  exact covered prefix). No match so far.
* Paragraph-5 singleton sets: same coverage, same result.
* A checksum-valid arrangement alone is NOT evidence of anything — 1/16 of
  all arrangements are checksum-valid by chance.

## If a match is ever produced

The match file records word indices and derivation parameters only. The
full mnemonic would be kept out of the public repository while funds remain
in the wallet; a redacted proof (hashes of word positions, checksum bits,
derivation path, and the reproduction commands) would be published here,
along with responsible-disclosure notes to the puzzle author. The tools for
that redacted proof already exist (`scripts/verify_target.py --json`).

## Working hypothesis for the extraction rule (not a claim)

The story's emphasis — the dream sentence "revealing words like maze, fury,
and renew", the second `Echo's` at the exact 512-token midpoint, the
`cryptic ... cryptic` bracket at 249/274 — points at the midpoint row as the
carrier of the hidden words.  The unresolved part is the ORDER rule
("arranged correctly"). If the full no-checksum scan of that set finishes
negative, the next families are: same set with passphrase/non-standard
path; paragraph-5 variants; and combinations with the 33-bit selector
story-numbers.
