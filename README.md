# Slonimsky Thesaurus Lab

An algorithmic reconstruction of Nicolas Slonimsky's *Thesaurus of Scales and
Melodic Patterns* (1947). It includes a practice UI, and research tools that
test how much of the book an algorithm can explain.

* **Generates** every pattern type in the book's twelve progression chapters
  (3,680 patterns) from a handful of rules: equal divisions of the octave(s),
  plus notes added by *interpolation*, *infrapolation* and *ultrapolation*.
* **Checks itself against the book** using 71 published facts about pattern
  numbers. The book's order is reproduced in every section that can be
  tested. In 5 sections the numbering matches exactly, which predicts 31 book
  numbers. The larger sections are in-order selections. The results are in
  [docs/FINDINGS.md](docs/FINDINGS.md).
* **Practice UI:** notation, playback, a pitch-class clock, keyboard, key
  cycling, learned-pattern tracking, MIDI/ABC export, and a pattern builder
  that names any cell the way Slonimsky would.

Pure Python (3.10+, no dependencies). The UI is plain HTML/JS served by
Python, with notation by the vendored [abcjs](https://www.abcjs.net).

## Quick start

```bash
pip install -e .            # or: export PYTHONPATH=src
slonimsky serve --open      # UI at http://127.0.0.1:8000
```

No install at all: `PYTHONPATH=src python -m slonimsky serve`.

## Command line

```bash
slonimsky chapters                          # the 12 progressions
slonimsky sections ditone                   # a chapter's sections
slonimsky list sesquitone inter-ultra       # patterns, with collections and 12-tone rows
slonimsky show ditone:-1,2,9 --abc          # explain, realize, analyse one pattern
slonimsky show tritone 1 --root F#3 --direction updown
slonimsky classify ditone C4 B3 D4 A4       # name any cell (octaves fix the register)
slonimsky classify whole-tone C B           # ...or list every register reading
slonimsky midi quadritone:1,3,6 --tempo 120 -o q.mid
slonimsky fit                               # score the reconstruction against the book
slonimsky --contour any fit                 # same, allowing zig-zag contours
slonimsky catalog -o catalog.json           # everything, as JSON
slonimsky build-site site --single-file     # the UI as one self-contained HTML file
```

A pattern id is `<chapter>:<offsets>`: semitone offsets of the added notes
from the principal tone. So `ditone:-1,2,9` is C, B (below), D (between),
A (above the next principal E), sequenced up C–E–G♯–C.

## How it works

```
progressions.py   the 12 chapters: N octaves divided into M parts (principal interval P)
cells.py          roles (infra / inter / ultra), Slonimsky's section names, classification
thesaurus.py      the generative rules: windows, ordering, filters -> sections -> patterns
realize.py        cell -> notes over a full cycle (up, down = mirrored, up & back; folding)
analysis.py       pitch-class sets, prime forms, symmetric-scale names, twelve-tone rows
anchors.py        published book numbers, placing them, scoring each section
notation.py, midi.py, catalog.py, server.py, cli.py
web/              the UI; engine.js mirrors realize/notation/cells/analysis for the browser
```

The rules and the evidence for each are in the docstring of `thesaurus.py`
and in [docs/FINDINGS.md](docs/FINDINGS.md). They are plain data (`Rules`),
so alternative hypotheses are one argument away:

```python
from slonimsky import Rules
from slonimsky.anchors import fit, fit_summary
print(fit_summary(fit(rules=Rules(contour="any", mixed_infra_reach=1))))
```

## Helping the research

The open question is *which* patterns Slonimsky kept in the large sections.
That needs ground truth. If you have the book, transcribe a run of patterns
into `src/slonimsky/data/anchors.csv`:

```
number,progression,label,cell,source,note
394,sesquitone,Interpolation of Two Notes,0 1 2,"my copy, p. 32",
```

`cell` is the first cell's pitch classes from C (`0 11 2 9`). Write signed
offsets (`0 -1 +2 +9`) to pin the register as well; otherwise every reading is
tried. Then run `slonimsky fit`.
`scripts/fetch_anchors.py` regenerates the published anchors from their
source.

## Development

```bash
pip install -e '.[dev]'
pytest                 # includes a Python/JS parity test when Node is installed
```

## Credits

* Anchors: Mark Gotham & Jason Yust, *Serial Analysis: A Digital Library of
  Rows in the Repertoire* (DLfM 2021), via their
  [Serial_Analyser](https://github.com/MarkGotham/Serial_Analyser) anthology;
  J. Bair (2003) for #286.
* Notation: [abcjs](https://www.abcjs.net) 6.7.1, MIT, vendored in
  `src/slonimsky/web/vendor/` with its license.

This project reproduces no pages or notation from the Thesaurus. It
generates patterns from rules and cites pattern numbers as facts. The book
is worth owning.
