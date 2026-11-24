# Data directory

## `english.txt` — the official BIP39 English wordlist

* Source: <https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt>
* SHA-256: `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`
* 2048 unique entries; the BIP39 wordlists are placed in the public domain
  by their author.  The hash is verified at load time
  (`echoquest.wordlists.load_wordlist`), and the test suite re-checks it.
* To re-verify independently:
  `curl -s <url> | sha256sum` must print the hash above.

## `electrum_old_wordlist.txt` — Electrum legacy seed wordlist

* Source: <https://raw.githubusercontent.com/spesmilo/electrum/master/electrum/old_wordlist>
* 1626 unique entries; MIT-licensed upstream (see
  docs/THIRD_PARTY_COPYRIGHT.md).
* Used only for read-only compatibility checks of the Electrum 1.x seed
  format (`echoquest.electrum`).  Research-relevant fact locked by tests:
  `maze`, `fury`, `renew` are **not** in this list, so the puzzle phrase
  cannot be a legacy Electrum seed containing the dream words.

## `synthetic_fixture.txt` — CI-safe synthetic story stand-in

A short original text (not the copyrighted puzzle story) with planted
structure: title + 3 paragraphs, several `echo`/`grace`/`shade` markers and
the three dream words.  Used by the test suite so CI never needs the real
story.  SHA-256:
`a90833bcffd70afca2a25dc586091ab41727808b28f5dcea5cf233763763b7233c6`.

## `source_provenance.json`, `expected_counts.json`

Provenance of the puzzle sources (URLs, dates, hashes — no story content)
and the independently verified positional facts for the story (used by the
reproduction scripts to check a fresh local copy).

## Obtaining the story (NOT redistributed here)

The story text is published by the puzzle author in the YouTube video
description of `https://www.youtube.com/watch?v=k5WIlZcXJHI`.  Place your
legally obtained copy at `private/story_original.txt` (git-ignored).  The
research copy this project was built from hashes (SHA-256, UTF-8, LF
newlines) to `437cb737531ee38ddce9aa7a4dd5dc4f68dd849d1aea54198735cda53a9a5db0`;
verify with `python -m echoquest ingest --input private/story_original.txt`.
