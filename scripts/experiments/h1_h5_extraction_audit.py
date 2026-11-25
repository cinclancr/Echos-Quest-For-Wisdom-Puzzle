#!/usr/bin/env python3
"""H1-H5 extraction-rule audit on the byte-exact story (Stage 2/3, 2026-11-25).

Every hypothesis below is implemented as executable code with an exact
tokenizer, exact boundaries and preregistered rule batteries; matched
negative controls and null models quantify chance.  No rule is tuned to
the answer: the dream words ``maze``/``fury``/``renew`` are the held-out
validation trio (H1) — rules that fail to recover all three independently
are recorded as rejected, not patched.

H1  dream-word anchor + a single extraction rule (positional/sentence/
    paragraph/narrative marker operations).
H2  story metatext as extraction instructions (first/last/inner words of
    marker sentences, narrative-event order, boundary-to-centre reads,
    repeated-word "Echo operators").
H3  512-token grid as deliberate construction (16x32 / 32x16 / 16-token
    folds, sentence-boundary alternatives, apostrophe tokenizer variant,
    one-token-edit sensitivity, whole-story window census).
H4  paragraph-5 unique-word mechanism (first/final four sentences,
    skip-marker interpretations, motivation audit for dropping
    ``next`` or ``hint``).
H5  frequency and recurrence (twice/once-per-half words, proper-name
    markers, frequency- and structure-preserving null models).

Controls: token-shuffle and sentence-shuffle nulls, random window shifts,
anchor-matched alternatives; per-family rule counts feed a Bonferroni-style
multiple-testing bound.

Input: private/story_original.txt (git-ignored, hash-pinned).
Output: results/scan/h1_h5_audit.json (non-secret) and
         results/scan/h3_window_census.csv.
Exit status is always 0 unless the story is missing/tampered.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from echoquest import STORY_SHA256  # noqa: E402
from echoquest.sources import load_story  # noqa: E402
from echoquest.tokenizers import tokenize  # noqa: E402
from echoquest.wordlists import load_wordlist  # noqa: E402

DREAM_TRIO = ("maze", "fury", "renew")  # prespecified held-out validation set
N_NULL = 2000  # iterations for each null model
SEED = 20261125


def bip39_window(tokens, wl):
    """Distinct literal BIP39 words of a token list (order-preserving)."""
    seen: list[str] = []
    for t in tokens:
        if t.text in wl and t.text not in seen:
            seen.append(t.text)
    return seen


def rule_report(name, family, words, positions, extra=""):
    """Standard record for one rule output.

    Candidate criterion: the hidden phrase is echo + 11 other words, so a
    rule is a complete candidate iff it recovers all three held-out dream
    words AND outputs either exactly 12 words including echo, or exactly
    11 words without echo.
    """
    trio_hit = [w for w in DREAM_TRIO if w in words]
    complete = (len(trio_hit) == 3 and
                (("echo" in words and len(words) == 12) or
                 ("echo" not in words and len(words) == 11)))
    return {
        "rule": name,
        "family": family,
        "words": words,
        "positions": positions,
        "word_count": len(words),
        "non_echo_word_count": len(words) - (1 if "echo" in words else 0),
        "recovers_dream_trio": len(trio_hit) == 3,
        "recovers_trio_members": trio_hit,
        "extra": extra,
        "verdict": "CANDIDATE" if complete else
                   ("trio-recovered-incomplete" if len(trio_hit) == 3 else "rejected"),
    }


def main() -> int:
    story_path = REPO / "private" / "story_original.txt"
    if not story_path.is_file():
        print("story copy missing (private/story_original.txt)", file=sys.stderr)
        return 2
    src = load_story(story_path, STORY_SHA256)
    wl = set(load_wordlist())
    tt = tokenize(src.text, "dcode")
    ta = tokenize(src.text, "apostrophe")
    tokens = tt.tokens
    n = len(tokens)
    rng = random.Random(SEED)
    out: dict = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "story_sha256": src.sha256,
        "token_counts": {"dcode": n, "apostrophe": len(ta.tokens)},
        "dream_trio_heldout": list(DREAM_TRIO),
    }

    # ------------------------------------------------------------- H1 ----
    h1_rules = []
    dream_positions = {w: tt.indices_of(w) for w in DREAM_TRIO}
    out["h1_dream_word_positions"] = dream_positions

    # R1: sentence(s) containing all three dream words
    dream_sents = [s for s in tt.sentences
                   if all(w in s.text.lower().split() or w in s.text.lower() for w in DREAM_TRIO)]
    for s in dream_sents:
        toks = [t for t in tokens if t.sentence == s.index]
        # story-copyright hygiene: never embed verbatim sentence text in a
        # published artifact — identify the sentence by position + sha256.
        s_sha = hashlib.sha256(s.text.lower().encode("utf-8")).hexdigest()
        h1_rules.append(rule_report(
            f"sentence-of-trio (sentence {s.index}/p{s.paragraph})", "sentence",
            bip39_window(toks, wl), [t.index for t in toks],
            f"sentence {s.index} of the pinned story (sha256 {s_sha[:16]}...)"))
    # R1b: every sentence containing any dream word
    any_dream_sents = sorted({s.index for s in tt.sentences
                              if any(w in s.text.lower() for w in DREAM_TRIO)})
    toks = [t for t in tokens if t.sentence in any_dream_sents]
    h1_rules.append(rule_report(
        f"sentences-containing-any-trio-word {any_dream_sents}", "sentence",
        bip39_window(toks, wl), [t.index for t in toks]))

    # R2: paragraph containing the dream words
    dream_paras = sorted({t.paragraph for t in tokens if t.text in DREAM_TRIO})
    for p in dream_paras:
        toks = [t for t in tokens if t.paragraph == p]
        h1_rules.append(rule_report(
            f"paragraph-of-trio (paragraph {p})", "paragraph",
            bip39_window(toks, wl), [t.index for t in toks]))
    # R2b: paragraph +/- 1
    for p in dream_paras:
        for dp in (p - 1, p + 1):
            toks = [t for t in tokens if t.paragraph == dp]
            h1_rules.append(rule_report(
                f"paragraph-plus-minus-one (paragraph {dp})", "paragraph",
                bip39_window(toks, wl), [t.index for t in toks]))

    # R3: fixed +/- k window around each dream word
    for k in (3, 5, 7, 10, 15):
        toks = []
        for w in DREAM_TRIO:
            for pos in tt.indices_of(w):
                toks += [t for t in tokens if abs(t.index - pos) <= k]
        h1_rules.append(rule_report(
            f"window+-{k}-around-trio", "positional-window",
            bip39_window(toks, wl), sorted({t.index for t in toks})))

    # R4/R5: first/last BIP39 word of each sentence in the dream paragraph
    for p in dream_paras:
        sent_ids = sorted({t.sentence for t in tokens if t.paragraph == p})
        for label, pick in (("first", 0), ("last", -1)):
            toks = []
            for sid in sent_ids:
                stoks = [t for t in tokens if t.sentence == sid and t.text in wl]
                if stoks:
                    toks.append(stoks[pick])
            h1_rules.append(rule_report(
                f"{label}-bip39-word-of-each-sentence-in-paragraph-{p}", "marker",
                bip39_window(toks, wl), [t.index for t in toks]))

    # R6: fixed token offset d from each dream word
    for d in range(-4, 5):
        if d == 0:
            continue
        toks = []
        for w in DREAM_TRIO:
            for pos in tt.indices_of(w):
                idx = pos + d
                if 1 <= idx <= n:
                    toks.append(tt.token_at(idx))
        h1_rules.append(rule_report(
            f"token-at-dream-position-plus-{d}", "offset",
            bip39_window(toks, wl), sorted({t.index for t in toks})))

    # R7: previous/next sentence of each dream sentence
    dream_sent_ids = sorted({t.sentence for t in tokens if t.text in DREAM_TRIO})
    for label, dd in (("prev", -1), ("next", 1)):
        ids = [s + dd for s in dream_sent_ids]
        toks = [t for t in tokens if t.sentence in ids]
        h1_rules.append(rule_report(
            f"{label}-sentence-of-dream-sentences {ids}", "sentence",
            bip39_window(toks, wl), [t.index for t in toks]))

    out["h1_rules"] = h1_rules
    out["h1_rule_count"] = len(h1_rules)
    out["h1_candidates_complete"] = [r["rule"] for r in h1_rules
                                      if r["verdict"] == "CANDIDATE"]
    out["h1_rules_recovering_trio"] = sum(r["recovers_dream_trio"] for r in h1_rules)

    # ------------------------------------------------------------- H2 ----
    MARKERS = ["decipher", "clues", "lie", "path", "answers", "within",
               "whispers", "cry", "falcon", "map", "pages", "book",
               "maze", "renew", "shade", "grace"]
    marker_sents = [s for s in tt.sentences
                    if any(m in s.text.lower().split() for m in MARKERS)]
    h2 = {"marker_lexicon": MARKERS,
          "marker_sentence_indices": [s.index for s in marker_sents]}
    # first / last / middle word and first/last BIP39 word of each marker sentence
    for label, pick in (("first-word", 0), ("last-word", -1),
                        ("middle-word", None)):
        toks = []
        for s in marker_sents:
            stoks = [t for t in tokens if t.sentence == s.index]
            if not stoks:
                continue
            if pick is None:
                toks.append(stoks[len(stoks) // 2])
            else:
                toks.append(stoks[pick])
        h2[f"marker-sentence-{label}"] = rule_report(
            f"{label} of each marker sentence", "metatext",
            bip39_window(toks, wl), [t.index for t in toks])
    for label, pick in (("first-bip39", 0), ("last-bip39", -1)):
        toks = []
        for s in marker_sents:
            stoks = [t for t in tokens if t.sentence == s.index and t.text in wl]
            if stoks:
                toks.append(stoks[pick])
        h2[f"marker-sentence-{label}"] = rule_report(
            f"{label} of each marker sentence", "metatext",
            bip39_window(toks, wl), [t.index for t in toks])
    # narrative event order
    EVENTS = ["village", "forest", "castle", "book", "return"]
    h2["narrative_events"] = {}
    for ev in EVENTS:
        posl = tt.indices_of(ev)
        toks = []
        for pos in posl:
            sid = tt.token_at(pos).sentence
            toks += [t for t in tokens if t.sentence == sid and t.text in wl]
        h2["narrative_events"][ev] = rule_report(
            f"bip39-words-of-sentences-containing-{ev}", "narrative",
            bip39_window(toks, wl), sorted({t.index for t in toks}))
    # boundary-to-centre: first+last token of each paragraph, then inward
    para_toks = {}
    for t in tokens:
        para_toks.setdefault(t.paragraph, []).append(t)
    b2c = []
    for p, ptoks in sorted(para_toks.items()):
        i, j = 0, len(ptoks) - 1
        while i < j and len(b2c) < 64:
            b2c.append(ptoks[i])
            b2c.append(ptoks[j])
            i += 1
            j -= 1
    h2["boundary-to-centre"] = rule_report(
        "outermost-token-pairs-of-each-paragraph-inward", "geometry",
        bip39_window(b2c, wl), [t.index for t in b2c])
    # repeated words as Echo operators (count == 2 anywhere)
    counts = tt.counts()
    twice = [w for w, c in counts.items() if c == 2]
    toks = [t for t in tokens if counts[t.text] == 2]
    h2["repeated-words-as-echo-operators"] = rule_report(
        "all-words-occurring-exactly-twice", "metatext",
        bip39_window(toks, wl), sorted({t.index for t in toks}),
        extra=f"{len(twice)} words occur twice; BIP39 among them: "
              f"{[w for w in twice if w in wl]}")
    out["h2"] = h2

    # ------------------------------------------------------------- H3 ----
    h3: dict = {}
    # window census: every 32-token window, distinct BIP39 count
    census = []
    for start in range(1, n - 31):
        win = tokens[start - 1:start + 31]
        census.append((start, len(bip39_window(win, wl))))
    mid_count = dict(census)[257]
    ge12 = [s for s, c in census if c >= 12]
    ge11 = [s for s, c in census if c >= 11]
    maxc = max(c for _, c in census)
    h3["window_census_32"] = {
        "windows_checked": len(census),
        "max_distinct_bip39": maxc,
        "windows_with_12_or_more": ge12,
        "windows_with_11_or_more": ge11,
        "midpoint_window_257": mid_count,
        "rank_of_midpoint": sorted(census, key=lambda x: (-x[1], x[0])).index((257, mid_count)) + 1,
        "windows_ge12_that_start_with_echo": [s for s, c in census if c >= 12
                                                and tokens[s - 1].text == "echo"],
        "windows_ge12_that_contain_echo": [s for s, c in census if c >= 12
                                            and any(t.text == "echo" for t in tokens[s - 1:s + 31])],
    }
    with (REPO / "results" / "scan" / "h3_window_census.csv").open("w") as fh:
        w = csv.writer(fh)
        w.writerow(["window_start", "distinct_bip39"])
        w.writerows(census)
    # grids
    h3["grid_16x32"] = {f"row {i+1} (tokens {32*i+1}-{32*i+32})":
                        len(bip39_window(tokens[32 * i:32 * i + 32], wl))
                        for i in range(16)}
    h3["grid_32x16"] = {f"row {i+1} (tokens {16*i+1}-{16*i+16})":
                        len(bip39_window(tokens[16 * i:16 * i + 16], wl))
                        for i in range(32)}
    h3["fold_16token_groups"] = {f"group {i+1}": len(bip39_window(tokens[16 * i:16 * i + 16], wl))
                                  for i in range(32)}
    # sentence-pair windows (sentence-boundary alternative)
    sp = {}
    for a in range(1, len(tt.sentences)):
        ids = (a, a + 1)
        toks = [t for t in tokens if t.sentence in ids]
        sp[f"sentences {a}-{a+1}"] = len(bip39_window(toks, wl))
    h3["sentence_pair_windows"] = sp
    h3["sentence_pair_windows_best"] = max(sp.items(), key=lambda kv: kv[1])
    # apostrophe tokenizer variant
    ta_tokens = ta.tokens
    na = len(ta_tokens)
    echo_pos_a = [t.index for t in ta_tokens if t.text.split("'")[0] == "echo"]
    h3["apostrophe_tokenizer"] = {
        "tokens": na,
        "echo_positions": echo_pos_a,
        "midpoint_window_254_285": len(bip39_window(ta_tokens[253:285], wl)),
        "window_counts_around_second_echo": {},
    }
    for pos in echo_pos_a[1:2]:
        for off in (0, -1, 1):
            win = ta_tokens[pos - 1 + off: pos - 1 + off + 32]
            h3["apostrophe_tokenizer"]["window_counts_around_second_echo"][f"start {pos+off}"] = \
                len(bip39_window(win, wl))
    # one-token sensitivity around the dCode midpoint
    sens = {}
    for shift in (-2, -1, 0, 1, 2):
        start = 257 + shift
        win = tokens[start - 1:start + 31]
        sens[f"window {start}-{start+31}"] = len(bip39_window(win, wl))
    h3["midpoint_window_sensitivity"] = sens
    # destiny's tokenisation sensitivity: merge destiny+s at 374/375 into one token
    h3["destinys_note"] = {
        "dcode": "destiny at 374 + s at 375 (two tokens)",
        "apostrophe": "destiny's single token; total 509, not 512",
        "conclusion": "512 = 2^9 depends on the apostrophe-splitting convention; "
                      "the apostrophe-preserving convention gives 509, so grid "
                      "alignment alone is weak evidence of design",
    }
    # probability under a frequency-preserving token shuffle of ANY 32-window
    # having >= 12 distinct BIP39 words:
    hits = 0
    word_pool = [t.text for t in tokens]
    for _ in range(N_NULL):
        rng.shuffle(word_pool)
        best = 0
        for start in range(0, len(word_pool) - 31):
            # distinct count in a sliding window via incremental sets (bounded)
            win = word_pool[start:start + 32]
            c = len({w for w in win if w in wl})
            if c > best:
                best = c
                if best >= 12:
                    break
        if best >= 12:
            hits += 1
    h3["null_shuffle_token_order"] = {
        "iterations": N_NULL,
        "any_window_ge12_distinct_bip39": hits,
        "p_value": hits / N_NULL,
    }
    # joint-alignment null: under a frequency-preserving shuffle, how often
    # is the 32-token window starting at the SECOND occurrence of the anchor
    # word (mirroring: 2nd "Echo's" at 257 anchors the midpoint row) as rich
    # as >= 12 distinct BIP39 words?
    def second_occurrence_window_rich(anchor: str, pool: list[str], thresh: int = 12) -> bool:
        pos2 = [i for i, w in enumerate(pool) if w == anchor]
        if len(pos2) < 2:
            return False
        start = pos2[1]
        win = pool[start:start + 32]
        return len({w for w in win if w in wl}) >= thresh
    joint_hits = {a: 0 for a in ("echo", "of", "to")}
    local_pool = [t.text for t in tokens]
    for _ in range(N_NULL):
        p2 = local_pool.copy()
        rng.shuffle(p2)
        for a in joint_hits:
            if second_occurrence_window_rich(a, p2):
                joint_hits[a] += 1
    h3["null_joint_alignment"] = {
        "iterations": N_NULL,
        "p_second_occurrence_window_ge12": {a: joint_hits[a] / N_NULL for a in joint_hits},
        "note": "mirrors the actual structure: anchor word's 2nd occurrence "
                "starts a 32-token window with >= 12 distinct BIP39 words; "
                "'of' and 'to' are frequency-matched alternative anchors "
                "(11 occurrences each, like echo)",
    }
    out["h3"] = h3

    # ------------------------------------------------------------- H4 ----
    h4: dict = {}
    p5_tokens = [t for t in tokens if t.paragraph == 5]
    p5_all = bip39_window(p5_tokens, wl)
    global_counts = counts
    p5_singletons = [w for w in p5_all if global_counts[w] == 1]
    h4["paragraph5_bip39_distinct"] = p5_all
    h4["paragraph5_global_singletons"] = p5_singletons
    p5_sent_ids = sorted({t.sentence for t in p5_tokens})
    h4["paragraph5_sentence_bip39"] = {}
    for sid in p5_sent_ids:
        toks = [t for t in p5_tokens if t.sentence == sid]
        h4["paragraph5_sentence_bip39"][sid] = bip39_window(toks, wl)
    first4 = p5_sent_ids[:4]
    last4 = p5_sent_ids[-4:]
    for label, ids in (("first-four-sentences", first4), ("final-four-sentences", last4)):
        toks = [t for t in p5_tokens if t.sentence in ids]
        h4[label] = rule_report(label, "paragraph5",
                                bip39_window(toks, wl), [t.index for t in toks])
    # occurrence context of next and hint (drop-choice motivation audit)
    for w in ("next", "hint"):
        ctx = []
        for t in tokens:
            if t.text == w:
                sid = t.sentence
                s = next(s for s in tt.sentences if s.index == sid)
                # redacted: position + sha256 only (no verbatim story text)
                ctx.append({
                    "token": t.index,
                    "sentence": sid,
                    "sentence_sha256": hashlib.sha256(
                        s.text.lower().encode("utf-8")).hexdigest(),
                })
        h4[f"context_{w}"] = {
            "occurrences": ctx,
            "global_count": global_counts[w],
            "is_global_singleton": global_counts[w] == 1,
        }
    # full-paragraph set with echo
    h4["paragraph5_with_echo"] = ["echo"] + p5_all if "echo" not in p5_all else p5_all
    h4["word_count_issue"] = (
        f"paragraph-5 distinct BIP39 words = {len(p5_all)}; +echo = "
        f"{len(h4['paragraph5_with_echo'])}; a 12-word phrase requires dropping "
        f"exactly one — no independent story-grounded rule selects which")
    out["h4"] = h4

    # ------------------------------------------------------------- H5 ----
    h5: dict = {}
    half = n // 2
    def once_each_half_words():
        """Words occurring exactly once in each 256-token half."""
        cfirst, csecond = Counter(), Counter()
        for t in tokens:
            if t.index <= half:
                cfirst[t.text] += 1
            else:
                csecond[t.text] += 1
        return [w for w in set(cfirst) | set(csecond)
                if cfirst[w] == 1 and csecond[w] == 1]
    once_half = once_each_half_words()
    once_half_bip39 = [w for w in once_half if w in wl]
    h5["once_in_each_half"] = {
        "all_words": sorted(once_half),
        "bip39_words": sorted(once_half_bip39),
        "bip39_count": len(once_half_bip39),
        "with_4letter_filter": sorted(w for w in once_half_bip39 if len(w) >= 4),
    }
    # proper names
    for name in ("echo", "grace", "shade"):
        h5[f"name_{name}"] = {"positions": tt.indices_of(name),
                               "count": counts.get(name, 0)}
    # exactly-twice words (any split)
    h5["twice_anywhere"] = sorted(w for w, c in counts.items() if c == 2)
    h5["twice_anywhere_bip39"] = sorted(w for w in h5["twice_anywhere"] if w in wl)

    # null model A: frequency-preserving token shuffle -> P(>=11 BIP39
    # words occur once in each half)
    def stat_once_each_half(pool):
        cfirst = Counter(pool[:half])
        csecond = Counter(pool[half:])
        sel = [w for w in set(pool)
               if cfirst[w] == 1 and csecond[w] == 1]
        return sum(1 for w in sel if w in wl)
    observed = stat_once_each_half([t.text for t in tokens])
    hits = 0
    pool = [t.text for t in tokens]
    for _ in range(N_NULL):
        p2 = pool.copy()
        rng.shuffle(p2)
        if stat_once_each_half(p2) >= 11:
            hits += 1
    h5["null_A_frequency_preserving_shuffle"] = {
        "iterations": N_NULL,
        "observed_once_each_half_bip39": observed,
        "ge11_hits": hits,
        "p_value": hits / N_NULL,
        "note": "shuffle destroys positional structure; measures chance of the "
                "once-in-each-half BIP39 richness under random placement",
    }
    # null model B: sentence-order shuffle within paragraphs (paragraph
    # structure + punctuation preserved)
    para_sentence_ids = {}
    for t in tokens:
        para_sentence_ids.setdefault(t.paragraph, set()).add(t.sentence)
    # build sentence -> (paragraph, ordered token texts)
    sent_tokens = {}
    for t in tokens:
        sent_tokens.setdefault(t.sentence, []).append(t.text)
    hits_b = 0
    for _ in range(N_NULL):
        # shuffle sentence order within each paragraph
        for p, sids in para_sentence_ids.items():
            lst = list(sids)
            rng.shuffle(lst)
            for rank, sid in enumerate(lst):
                pass  # positions recomputed below via concatenated order
        # simpler: shuffle the list of sentence token-lists within paragraphs
        order = []
        for p in sorted(para_sentence_ids):
            sl = [list(sent_tokens[s]) for s in sorted(para_sentence_ids[p])]
            rng.shuffle(sl)
            order += sl
        flat = [w for s in order for w in s]
        if stat_once_each_half(flat) >= 11:
            hits_b += 1
    h5["null_B_sentence_order_shuffle"] = {
        "iterations": N_NULL,
        "ge11_hits": hits_b,
        "p_value": hits_b / N_NULL,
        "note": "preserves paragraph membership, sentence composition and "
                "word frequencies; shuffles only sentence order",
    }
    out["h5"] = h5

    # --------------------------------------------- Stage-3 shared controls --
    controls: dict = {}
    # random 32-window shifts: distribution of distinct-BIP39 counts
    shift_counts = []
    for _ in range(N_NULL):
        start = rng.randint(1, n - 31)
        win = tokens[start - 1:start + 31]
        shift_counts.append(len(bip39_window(win, wl)))
    controls["random_window_shift"] = {
        "iterations": N_NULL,
        "mean": sum(shift_counts) / len(shift_counts),
        "max": max(shift_counts),
        "ge12_fraction": sum(c >= 12 for c in shift_counts) / len(shift_counts),
        "midpoint_window": mid_count,
    }
    # anchor-matched alternatives: words occurring exactly as often as echo
    echo_count = counts["echo"]
    anchors = [w for w, c in counts.items() if c == echo_count and w != "echo"]
    controls["anchor_matched_alternatives"] = {
        "echo_occurrence_count": echo_count,
        "alternative_anchors_same_frequency": anchors,
        "second_occurrence_window_bip39_counts": {},
    }
    for a in anchors:
        posl = tt.indices_of(a)
        if len(posl) >= 2:
            pos = posl[1]  # second occurrence, mirroring Echo's at 257
            win = tokens[pos - 1:pos + 31]
            controls["anchor_matched_alternatives"][
                "second_occurrence_window_bip39_counts"][a] = len(bip39_window(win, wl))
    out["controls"] = controls

    # multiple-testing bound
    rule_total = len(h1_rules)
    out["multiple_testing"] = {
        "h1_rules_tested": rule_total,
        "h2_rule_families": 4 + len(EVENTS) + 2,
        "bonferroni_note": f"any p-value from H1/H2 families should be seen "
                           f"against >= {rule_total} tested rules (Bonferroni "
                           f"x{rule_total})",
    }

    dest = REPO / "results" / "scan" / "h1_h5_audit.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    # console summary
    print(f"tokens dcode={n} apostrophe={na}")
    print(f"H1: {rule_total} preregistered rules; recovering trio: "
          f"{out['h1_rules_recovering_trio']}; complete candidates: "
          f"{out['h1_candidates_complete']}")
    print(f"H3: 32-token windows >=12 distinct BIP39: {ge12}; >=11: {ge11}; "
          f"midpoint={mid_count} (rank {h3['window_census_32']['rank_of_midpoint']})")
    print(f"H3 null (token shuffle, any window >=12): p={h3['null_shuffle_token_order']['p_value']}")
    print(f"H3 joint-alignment null (2nd occurrence anchors): "
          f"{h3['null_joint_alignment']['p_second_occurrence_window_ge12']}")
    print(f"H5 once-each-half BIP39: {h5['once_in_each_half']['bip39_count']} "
          f"(null-A p={h5['null_A_frequency_preserving_shuffle']['p_value']}, "
          f"null-B p={h5['null_B_sentence_order_shuffle']['p_value']})")
    print(f"controls: random-shift max={controls['random_window_shift']['max']} "
          f"mean={controls['random_window_shift']['mean']:.2f}")
    print(f"written: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
