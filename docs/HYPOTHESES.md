# Hypotheses ledger

Extraction-rule families investigated for the eleven hidden words (word 1 is
`echo`, pinned by the author).  Status tags: VERIFIED / HYPOTHESIS /
UNTESTED / REJECTED / INCOMPLETE.  Machine-readable registry:
`src/echoquest/hypotheses.py` (printed via `python -m echoquest hypotheses`).

## A. Cross-half singleton words (`once-in-each-half`)

* Rule: tokens appearing exactly once in each 256-token half; BIP39 member;
  ≥4 letters (the letter filter is NOT story-grounded).
* Set (11 + echo): `upon there wise often wide young remember journey find
  real ancient`.
* Status: REJECTED as a natural-order phrase at path m/44'/0'/0'/0/0 with
  empty passphrase (no checksum, no address match) and as a tested set of
  structured permutations at that path; the "22 crossing pairs" geometry is
  not statistically rare under randomisation controls (prior work, audited).
  The word-set hypothesis itself remains open only via new extraction
  evidence — no such evidence exists today.

## B. Twice-and-four-letters

* Set: `upon wise wide help will find real into them like gold` (11 + echo);
  `them` is not BIP39 (prefix completion → `theme` unsupported by the text).
* Status: REJECTED (no address match in natural or tested derived orders;
  completion unmotivated).

## C. Dream sentence words

* Set: the dream sentence's BIP39 words `they echo more vivid night like
  maze fury renew hint` — only 10 words.
* Status: INCOMPLETE — not a 12-word construction without unmotivated padding.

## D. Midpoint row 257–288 (`midpoint-32`) — currently top-ranked

* Rule: the 32-token row beginning at the second `Echo's` (the exact 512/2+1
  midpoint) contains 12 distinct BIP39 words; `like` deduplicated.
* Set: `echo more vivid night like maze fury renew hint what they upon`.
* All Electrum-standard permutations rejected (m/0/0) — see RESULTS.md.
* Full no-checksum BIP39 permutation scan: in progress (block 0 at 28.3%,
  446,464 derivations, 0 matches so far; checkpointed and resumable).
* **Audit (2026-11-25): the row's BIP39 density is NOT statistically
  special** — 50 of 481 32-token windows carry ≥ 12 distinct BIP39 words
  (max 14, this row ranks 48th), ±1-token shifts give 11, and the joint
  anchor-alignment null gives p = 0.1305. The set stays top-ranked for its
  content (all three dream words at the narrative midpoint), and the
  running wallet scan — not statistics — will decide it.
* Status: HYPOTHESIS (statistical aura falsified; content coincidence
  remains).

## E. Paragraph-5 singleton BIP39 words (`p5-singletons`)

* Set: `next morning armed nothing strong more vivid night maze fury renew
  hint` (+ echo = 13; drop `next` as instruction or `hint` → 12 words).
* Historical index errors (armed/strong) were corrected and re-audited.
* Electrum-standard permutations (both drop variants): REJECTED at m/0/0.
* Audit (2026-11-25): the singleton set is EXACTLY 12 words (verified), so
  +echo = 13 forces exactly one drop with no story-grounded selector
  (next lives only in "The next morning…"; hint only in "Each a cryptic
  hint…"); first-4/final-4 sentence variants introduce non-singletons.
* Status: HYPOTHESIS but weakened — the drop-one rule is unmotivated and
  both variants are rejected in natural orders and at Electrum m/0/0.

## F. Echo/Grace parity set

* Set: `upon shade there wise often wide day remember find cry turned`.
  Membership audit (2026-11-25): the literal token `shade` is **NOT** a
  BIP39 word (the official list has `shadow`, index 1574, but not
  `shade`); `turned` and `cry` are not BIP39 words either.  The prefix
  completions `shade→shadow` and `turned→turn` are explicit, text-unmotivated
  transformations and are flagged as such.  Earlier drafts of this ledger
  wrongly asserted "literal `shade` IS a BIP39 word" — corrected and locked
  by `tests/test_wordlist.py::test_shade_is_not_a_bip39_word_shadow_is`.
* Status: REJECTED as a natural-order phrase at the primary path
  (no checksum, no address match, both with and without the prefix
  completions); arbitrary permutations were partially tested in prior
  phases.  As a word-set hypothesis this is among the weakest: at least two
  of its eleven words require non-literal transformations.

## G. Alternate-position set

* Set: `upon there old wide young visions remember find cry them turned`
  with completions `visions→visit`, `them→theme`, `turned→turn`.
* Status: REJECTED for natural orders; prior structured permutations failed.

## H. Acrostics / grids / positional codes

* dCode-style acrostic outputs (W1/W2/W3, W→/L, WnLn), 16×32 grid paths,
  A1Z26 of GRACE/SHADE, row/column traversals — all produce non-BIP39 words
  or short lists; no 12-word phrase results.
* Status: REJECTED as direct extractors; remain documented in
  `results/extractions.csv`.

## I. Triads / 33-bit selectors

* 33 narrative units (title + 32 sentences) grouped as 11 triads; the dream
  words' 33 bits split into 11 3-bit selectors (4,2,3,0,5,7,1,6,6,6,1).
* Status: INCOMPLETE — no unique mapping from selectors to words is
  justified by the text; prior bounded tests found no unambiguous output.

## J. Electrum-format hypotheses

* Electrum 1.x legacy seeds: REJECTED (`maze`/`fury`/`renew` absent from
  the 1626-word list).
* Electrum 2.x standard seeds: all permutations of the top three sets
  carry ~155K valid version tags; each derived at `m/0/0` — REJECTED for
  those sets at that address index.  Non-zero address indices remain
  UNTESTED (available via the `electrum` mode of the C scanner).

## K. Wallet-side hypotheses (independent of word selection)

* BIP39 KDF with broken checksum at the primary path: the running full scan.
* Passphrases: 12 story-derived passphrases tested for natural orders
  (61,200 comparisons, 0 matches).  Arbitrary passphrases on arbitrary
  permutations: UNTESTED (combinatorial; requires dedicated search).
* Brainwallet (SHA256 of phrase as key): REJECTED for natural orders.
* Address index > 0 / alternate paths for permutations: partially tested
  (natural orders cover 15 paths; permutations only at the primary path).

## What would falsify the whole BIP39 model

If the full no-checksum scans of the top sets complete with zero matches at
the primary path (and reasonable extensions), the remaining explanations are
(a) a different word set (extraction rule still unknown), (b) a passphrase,
(c) a non-standard derivation, or (d) a non-BIP39 word source. Each has its
own bounded search documented in HOW_TO_REPRODUCE.md.
