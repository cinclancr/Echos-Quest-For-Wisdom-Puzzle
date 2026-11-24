# dCode-style analysis workflow

The maintainer's early analysis used the dCode "Acrostic" tool with the
setting "ignore all characters except letters and digits".  This project
re-implements that convention so results are reproducible without the
external tool:

1. Case-fold the text; strip punctuation; split on whitespace.
2. Apostrophes split words (`Echo's` -> `echo` + `s`).
3. The title counts as the first unit.

Outputs the maintainer supplied from dCode (recorded verbatim, do not
"correct" them):

* W2/L: `s upon day the Echo next after they turned smiled so`
* W3/L: `Quest a a forest asked morning what approached to her Echo`
* W1&2/L: `Echo s Once upon One day Ah the Determined Echo The next Finally after As they Echo turned Grace smiled And so`
* W→/L: `Wisdom understand concern path falcon goal air s pages them forest`
* W1&→/L: `Echo Wisdom Once understand One concern Ah path Determined falcon The goal Finally air As s Echo pages Grace them And forest`
* WnLn: `Echo upon a speaks you nothing eternity creaked amazement And a`
* WnLn reverse: `And smiled to the like nothing me are at there Echo`

All of these contain non-BIP39 words and none is a candidate mnemonic; they
are catalogued in results/extractions.csv for completeness. The project's
tokenisers (`echoquest.tokenizers`) reproduce the underlying token stream
(512 tokens), verified against the tool's output structure.
