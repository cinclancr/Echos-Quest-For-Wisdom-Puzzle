"""Extraction hypothesis registry: every method runs deterministically."""

from __future__ import annotations

from pathlib import Path

from echoquest.extractors import available, list_methods, run
from echoquest.tokenizers import tokenize

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_fixture.txt"
T = tokenize(FIXTURE.read_text("utf-8"), "dcode")


def test_registry_is_nonempty_and_sorted() -> None:
    methods = list_methods()
    assert len(methods) >= 20
    assert methods == sorted(methods)
    assert "midpoint-32" in methods
    assert "p5-singletons" in methods


def test_every_method_runs_and_is_deterministic() -> None:
    for m in list_methods():
        r1 = run(m, T)
        r2 = run(m, T)
        assert list(r1.words) == list(r2.words), m
        assert isinstance(r1.words, tuple)


def test_dream_words_extraction() -> None:
    r = run("dream-words", T)
    assert list(r.words) == ["maze", "fury", "renew"]


def test_acrostic_paragraph_first() -> None:
    r = run("acrostic-paragraph-first", T)
    # title + three paragraphs
    assert list(r.words) == ["echo", "once", "one", "and"]


def test_after_each_echo_is_honest_about_failures() -> None:
    # On this fixture the words following "echo" are not BIP39 words; the
    # method must report zero rather than invent words.
    r = run("after-each-echo", T)
    assert len(r.words) == 0


def test_available_map_has_descriptions() -> None:
    av = available()
    assert isinstance(av, dict)
    assert all(isinstance(v, str) and v for v in av.values())
