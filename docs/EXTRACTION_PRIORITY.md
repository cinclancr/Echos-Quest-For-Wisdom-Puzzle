# Extraction hypotheses — priority, controls, and ranking rationale

Written 2026-11-25, after the independent repo audit
(`docs/REPO_AUDIT_2026-11-25.md`). This file pre-registers the active
hypotheses, the falsification controls already executed against each, and
the ranking rationale that decides where the next compute goes.

Ranking principles (Stage 3.3): simplicity of the extraction rule, story
grounding, out-of-sample evidence (the held-out dream trio), and — only
AFTER those — checksum validity. Checksum validity is never used to rank:
1/16 of all arrangements are checksum-valid by chance.

## Priority table

| Rank | Hypothesis | Set (word order in files) | Controls executed | Verdict |
|---|---|---|---|---|
| 1 | midpoint-32 row (tokens 257–288) | `echo more vivid night like maze fury renew hint what they upon` | window census (rank 48/481), joint null p=0.13, ±1 sensitivity → 11 | ACTIVE — full no-checksum permutation scan running; not yet falsified as a word SET |
| 2 | p5-singletons with one dropped word | `next morning armed nothing strong more vivid night maze fury renew hint` + echo, drop `next` OR `hint` | drop-choice motivation audit (§H4) | OPEN but weak — 13 words for 12 slots, no grounded drop rule; both variants rejected at Electrum m/0/0 and in natural orders |
| 2b | **p5-final-four (H4 audit finding, 2026-11-25)** | `echo ancient into they more vivid night like maze fury renew hint` | natural battery: 4 orders × 12 passphrases × 2 KDFs × 15 paths × 2 encodings | **BATTERY-TESTED, 0 matches** — the only sentence-range rule reaching exactly 12 words (incl. echo + dream trio); weak because the "final four sentences" rule is not story-grounded and `ancient`/`into`/`they` are non-singletons (each occurs exactly twice in the story) |
| 3 | dream-sentence ± 15 tokens | `echo more vivid night like maze fury renew hint what they` | H1 battery | INCOMPLETE — 10 non-echo words; one word short of a phrase |
| — | cross-half singletons ("set A") | `upon there wise often wide young remember journey find real ancient` | frequency-preserving null p=0.409; ≥4-letter filter exposed | REJECTED as evidence — richness is chance; the 11-word size is a filter artifact |
| — | twice-anywhere BIP39 words | `upon wise wide help will find real into them like gold` (+ completions) | null models; membership audit | REJECTED — needs non-literal completions (`them→theme`) |
| — | acrostics/grids/codes (W1/W2, 16×32 paths, A1Z26, book cipher) | various short lists | extraction catalogue | REJECTED — outputs are non-BIP39 or far below 12 words |
| — | Electrum-format hypotheses | — | 3 sets × 11! Electrum-tag scans (0 matches); `maze`/`fury`/`renew` not in legacy wordlist | REJECTED at m/0/0 for the three top sets; deeper indices open via `electrum` mode |

## Pre-registered controls (all executed 2026-11-25)

1. **Token-shuffle null** (frequency preserved): any 32-token window with
   ≥ 12 distinct BIP39 words appears with p = 1.0 — window richness alone
   is not evidence of construction.
2. **Joint-alignment null**: the anchor's second occurrence starting a
   ≥ 12-rich window has p = 0.1305 for `echo` and ≈ 0.09 for
   frequency-matched alternatives (`of`, `to`) — the "second Echo's at
   512/2+1" alignment is not significant on its own.
3. **Sentence-order null** (paragraph structure preserved): p = 1.0 for
   the once-in-each-half statistic.
4. **Anchor-matched alternatives**: alternative anchors with the same
   occurrence count as `echo` (`of`, `to`) produce second-occurrence
   windows of 6 and 13 distinct BIP39 words — richer than chance, poorer
   than the myth of uniqueness (the real midpoint window has 12).
5. **One-token sensitivity**: shifting the midpoint window by ±1 yields
   11 distinct words — the 12-word result is not robust to the exact
   boundary, another reason not to treat "the 32-token row" as
   self-evidently the author's rule.
6. Multiple-testing bound: ≥ 22 rules per family were tested; any
   "significant" hit must survive a Bonferroni ×22 correction.

## What the audit changes in the research direction

The statistical aura around the midpoint row (512 = 2^9 tokens, second
`Echo's` at 257, "12 BIP39 words in one row") is **chance-compatible**:
50 of 481 windows are as rich or richer. What survives is only the
*coincidence of content*: the row happens to contain all three dream
words and the narrative midpoint. Therefore the row remains the top word
SET candidate, but its confirmation can no longer come from
statistics — only from the wallet scan itself (the running full no-checksum
permutation scan) or from finding a genuine story-grounded rule the
author could have intended.

## Next decisive experiments (ordered)

1. **Finish the full no-checksum scan of the midpoint-32 set** at
   `m/44'/0'/0'/0/0` (empty passphrase, both encodings) — the scan that
   decides the strongest candidate outright. Checkpointed, resumable;
   coverage in `results/summary.json`.
2. If (1) finishes negative: same set with the 12 story-derived
   passphrases (natural battery already covers natural orders only), then
   alternate paths for permutations (`electrum` mode covers m/0/1–4 and
   m/1/x for Electrum-valid phrases).
3. In parallel (cheap, story-side): extend the H1 battery with
   sentence-pair and dream-sentence-neighborhood rules that could output
   exactly 11 non-echo words; the H3 census CSV
   (`results/scan/h3_window_census.csv`) lists the other 49 rich windows —
   several overlap the ¶5/dream-sentence region and are worth reading as
   candidate rows (e.g., windows 258–261 contain the dream sentence
   interior).
4. Only with an independently supported extraction AND order: checksum,
   Electrum tags, standard paths first; bounded index range; passphrases
   last. Exact ledger of combinations in `results/summary.json`.
