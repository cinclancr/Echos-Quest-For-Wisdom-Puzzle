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
* Status: REJECTED as a solved phrase — natural orders fail checksum;
  structured permutations address-tested with no match.  The "22 crossing
  pairs" geometry is not statistically rare under randomisation controls
  (prior work, audited).

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

* Rule: the 32-token row beginning at the second `Echo's` (the exact 512/2
  midpoint) contains 12 distinct BIP39 words; `like` deduplicated.
* Set: `echo more vivid night like maze fury renew hint what they upon`.
* All Electrum-standard permutations rejected (m/0/0) — see RESULTS.md.
* Full no-checksum BIP39 permutation scan: in progress.
* Status: HYPOTHESIS (strongest story evidence: all three dream words and
  the second `Echo's` anchor live in this row).

## E. Paragraph-5 singleton BIP39 words (`p5-singletons`)

* Set: `next morning armed nothing strong more vivid night maze fury renew
  hint` (+ echo = 13; drop `next` as instruction or `hint` → 12 words).
* Historical index errors (armed/strong) were corrected and re-audited.
* Electrum-standard permutations (both drop variants): REJECTED at m/0/0.
* Status: HYPOTHESIS; the "drop one word" rule is the weak point.

## F. Echo/Grace parity set

* Set: `upon shade there wise often wide day remember find cry turned` with
  prefix completions `shade→shadow`, `turned→turn` (literal `shade` IS a
  BIP39 word — both variants tested).
* Status: REJECTED for natural orders (no checksum, no address match);
  arbitrary permutations were partially tested in prior phases.

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
