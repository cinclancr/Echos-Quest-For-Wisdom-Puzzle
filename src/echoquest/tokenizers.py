"""Pluggable tokenisers for the story text.

Two conventions are maintained throughout the research:

``dcode``
    Maximal runs of ``[A-Za-z0-9]+`` on the case-folded text; apostrophes
    split words (``Echo's`` -> ``echo`` + ``s``).  This mirrors the dCode
    acrostic tool convention the original solver screenshots used.  It
    yields 512 tokens for the supplied story (title included).

``apostrophe``
    Maximal runs of ``[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*`` on the case-folded
    text; possessives stay attached (``echo's``).  Yields 509 tokens for
    the supplied story.

Every token carries its 1-based absolute index, paragraph index and
character offsets so positional claims can be re-derived mechanically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

DCODE_RE = re.compile(r"[A-Za-z0-9]+")
APOS_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")

TOKENIZERS = ("dcode", "apostrophe")


@dataclass(frozen=True)
class Token:
    """A single token with 1-based position metadata."""

    index: int  # 1-based absolute index (title included)
    text: str  # case-folded surface form
    paragraph: int  # 0 = title, 1..10 = narrative paragraphs
    sentence: int  # 0 = title / non-sentence tokens, 1..32 = narrative sentences
    char_start: int
    char_end: int

    @property
    def clean(self) -> str:
        """Token with apostrophe-suffix stripped (``echo's`` -> ``echo``)."""
        return self.text.split("'")[0]


@dataclass(frozen=True)
class Paragraph:
    """A paragraph (0 = title)."""

    index: int
    text: str
    char_start: int
    char_end: int
    token_count: int


@dataclass(frozen=True)
class Sentence:
    """A punctuation-delimited narrative sentence (1-based, title excluded)."""

    index: int
    paragraph: int
    text: str
    token_count: int


@dataclass(frozen=True)
class TokenizedText:
    """Full tokenisation result."""

    name: str
    text: str
    tokens: tuple[Token, ...]
    paragraphs: tuple[Paragraph, ...]
    sentences: tuple[Sentence, ...]

    @property
    def words(self) -> list[str]:
        return [t.text for t in self.tokens]

    def indices_of(self, word: str) -> list[int]:
        w = word.lower()
        return [t.index for t in self.tokens if t.text == w]

    def token_at(self, index: int) -> Token:
        if not 1 <= index <= len(self.tokens):
            raise IndexError(f"token index {index} out of range 1..{len(self.tokens)}")
        return self.tokens[index - 1]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.tokens:
            out[t.text] = out.get(t.text, 0) + 1
        return out


def _split_paragraphs(text: str) -> list[tuple[str, int]]:
    """Split on blank lines, recording character offsets."""
    paras: list[tuple[str, int]] = []
    pos = 0
    chunks = re.split(r"\n\s*\n", text)
    for chunk in chunks:
        start = text.index(chunk, pos)
        paras.append((chunk, start))
        pos = start + len(chunk)
    return paras


def _split_sentences(paragraph_text: str) -> list[tuple[str, int]]:
    """Split narrative sentences on . ! ? boundaries (closing quote attached).

    Returns ``(sentence_text, offset_within_paragraph)`` pairs.
    """
    stitched: list[str] = []
    current = ""
    i = 0
    while i < len(paragraph_text):
        ch = paragraph_text[i]
        current += ch
        if ch in ".!?":
            # include a closing double quote immediately after
            if i + 1 < len(paragraph_text) and paragraph_text[i + 1] == '"':
                current += paragraph_text[i + 1]
                i += 1
            stitched.append(current)
            current = ""
            # skip inter-sentence whitespace
            j = i + 1
            while j < len(paragraph_text) and paragraph_text[j] in " \t":
                j += 1
            i = j
            continue
        i += 1
    if current.strip():
        stitched.append(current)
    sents: list[tuple[str, int]] = []
    pos = 0
    for s in stitched:
        start = paragraph_text.index(s, pos)
        sents.append((s, start))
        pos = start + len(s)
    return sents


def tokenize(text: str, tokenizer: str = "dcode") -> TokenizedText:
    """Tokenise ``text`` under the named convention.

    The text is treated as-is: the story file contains a title, blank lines
    and ten narrative paragraphs.  Paragraph 0 is the title block.
    """
    if tokenizer not in TOKENIZERS:
        raise ValueError(f"unknown tokenizer {tokenizer!r}; expected one of {TOKENIZERS}")
    pattern = DCODE_RE if tokenizer == "dcode" else APOS_RE
    lowered = text

    paras = _split_paragraphs(lowered)
    para_objects: list[Paragraph] = []
    tokens: list[Token] = []

    # Sentence inventory (narrative paragraphs only, excluding the title).
    sentence_objects: list[Sentence] = []
    sentence_no = 0

    abs_index = 0
    for p_idx, (p_text, p_start) in enumerate(paras):
        p_matches = list(pattern.finditer(p_text))
        # sentence segmentation for narrative paragraphs
        p_sentences: list[tuple[str, int]] = []
        if p_idx >= 1:
            p_sentences = _split_sentences(p_text)
        sentence_token_counts: dict[int, int] = {}
        for s_idx, (s_text, _s_off) in enumerate(p_sentences, start=1):
            sentence_no += 1
            cnt = len(pattern.findall(s_text))
            sentence_token_counts[s_idx] = cnt
            sentence_objects.append(
                Sentence(
                    index=sentence_no,
                    paragraph=p_idx,
                    text=s_text.strip(),
                    token_count=cnt,
                )
            )
        para_objects.append(
            Paragraph(
                index=p_idx,
                text=p_text,
                char_start=p_start,
                char_end=p_start + len(p_text),
                token_count=len(p_matches),
            )
        )
        # assign sentence numbers to tokens by scanning within each sentence
        sent_boundaries: list[tuple[int, int, int]] = []  # (start, end, sentence_no)
        running = 0
        for s_idx, (s_text, _off) in enumerate(p_sentences, start=1):
            cnt = sentence_token_counts[s_idx]
            sent_boundaries.append((running, running + cnt, sentence_no - len(p_sentences) + s_idx))
            running += cnt
        for m in p_matches:
            abs_index += 1
            local = sum(1 for mm in p_matches if mm.start() < m.start())
            sentence_id = 0
            for lo, hi, sid in sent_boundaries:
                if lo <= local < hi:
                    sentence_id = sid
                    break
            if p_idx == 0:
                sentence_id = 0
            tokens.append(
                Token(
                    index=abs_index,
                    text=m.group(0).lower(),
                    paragraph=p_idx,
                    sentence=sentence_id,
                    char_start=p_start + m.start(),
                    char_end=p_start + m.end(),
                )
            )

    return TokenizedText(
        name=tokenizer,
        text=text,
        tokens=tuple(tokens),
        paragraphs=tuple(para_objects),
        sentences=tuple(sentence_objects),
    )


def grid(tokens: Sequence[Token], columns: int) -> list[list[Token]]:
    """Arrange tokens row-major into ``ceil(n/columns)`` rows of ``columns``."""
    rows: list[list[Token]] = []
    toks = list(tokens)
    for i in range(0, len(toks), columns):
        rows.append(toks[i : i + columns])
    return rows


def acrostic_rows(tokens: Sequence[Token], row_length: int) -> list[list[str]]:
    """Row-major grid of surface forms (for acrostic-style inspection)."""
    return [[t.text for t in row] for row in grid(tokens, row_length)]


def find_positions(words: Iterable[str], tokens: Sequence[Token]) -> dict[str, list[int]]:
    """Map each word to its 1-based token indices (case-folded exact match)."""
    wanted = [w.lower() for w in words]
    out: dict[str, list[int]] = {w: [] for w in wanted}
    for t in tokens:
        if t.text in out:
            out[t.text].append(t.index)
    return out
