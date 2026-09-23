#!/usr/bin/env python3
"""Rebuild src/slonimsky/data/anchors.csv from its sources.

Main source: the Slonimsky entries in Gotham & Yust's *Serial Analyser*
anthology (https://github.com/MarkGotham/Serial_Analyser). It lists the
book's patterns whose first twelve notes form a twelve-tone row, with the
pattern number, the heading it appears under, and the row as pitch
classes starting on C. Only the facts we need are kept: number, chapter,
heading and the repeating cell (derived from the row).

A handful of further facts come from secondary literature and are listed
in MANUAL below with their sources.

Usage: python scripts/fetch_anchors.py [--csv local_copy.csv]
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/MarkGotham/Serial_Analyser/main/"
    "Repertoire_Anthology/rows_in_the_repertoire.csv"
)
SOURCE_NAME = "Gotham & Yust, Serial Analyser anthology (twelve-tone rows in the Thesaurus)"
OUT = Path(__file__).resolve().parents[1] / "src" / "slonimsky" / "data" / "anchors.csv"

CHAPTERS = {
    "Tritone": ("tritone", 6), "Ditone": ("ditone", 4), "Sesquitone": ("sesquitone", 3),
    "Whole-Tone": ("whole-tone", 2), "Semitone": ("semitone", 1),
    "Quadritone": ("quadritone", 8), "Sesquiquadritone": ("sesquiquadritone", 9),
    "Quinquetone": ("quinquetone", 10), "Diatessaron": ("diatessaron", 5),
    "Septitone": ("septitone", 14), "Diapente": ("diapente", 7),
    "Sesquiquinquetone": ("sesquiquinquetone", 11),
}

MANUAL = [
    # number, progression, label, cell pcs, source, note
    (1, "tritone", "Interpolation of One Note", "0 1",
     "Widely cited as pattern 1 (C C# F# G), e.g. the 'Using the Slonimsky Thesaurus' video series",
     ""),
    (10, "tritone", "Interpolation of Two Notes", "",
     "Secondary literature: pattern 10 is a tritone progression with two interpolated notes",
     "label only"),
    (286, "ditone", "Infra-Interpolation", "",
     "Bair (2003), UNT dissertation on Coltrane: #286 'ditone progression with infra-interpolation'",
     "label only; linked to Giant Steps"),
    (392, "sesquitone", "Interpolation of One Note", "0 1",
     "Widely cited: #392 is the half-whole octatonic (diminished) scale", ""),
    (393, "sesquitone", "Interpolation of One Note", "0 2",
     "Widely cited: #393 is the whole-half octatonic (diminished) scale", ""),
]


def derive_cell(row: list[int], interval: int) -> list[int] | None:
    """Shortest prefix k such that the row is that cell sequenced up by P."""
    for k in range(1, 9):
        if all((row[i + k] - row[i] - interval) % 12 == 0 for i in range(12 - k)):
            return row[:k]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", help="use a local copy of rows_in_the_repertoire.csv")
    args = ap.parse_args()
    if args.csv:
        text = Path(args.csv).read_text("utf-8")
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as r:
            text = r.read().decode("utf-8")
    rows = []
    for rec in csv.reader(io.StringIO(text)):
        if not rec or "Slonimsky" not in rec[0]:
            continue
        m = re.match(r"No\.\s*(\d+)([a-z]*)\s*(.*)", rec[1])
        if not m:
            continue
        title = m.group(3)
        chap = re.search(r"\((\S+) Progression", title)
        if not chap or chap.group(1) not in CHAPTERS:
            continue
        key, interval = CHAPTERS[chap.group(1)]
        label = title.split("(")[0].strip()
        pcs = [int(x) for x in rec[3:15]]
        cell = derive_cell(pcs, interval)
        if cell is None or len(cell) < 2:
            continue  # free permutations, or a bare scale with no added notes
        rows.append((int(m.group(1)), key, label, " ".join(map(str, cell)), SOURCE_NAME, ""))
    rows.extend(MANUAL)
    rows.sort(key=lambda r: r[0])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        f.write("# Anchors: published facts about Thesaurus pattern numbers.\n")
        f.write("# Regenerate with scripts/fetch_anchors.py. 'cell' = pitch classes of the\n")
        f.write("# repeating cell starting on C (register is not recorded by the sources).\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["number", "progression", "label", "cell", "source", "note"])
        w.writerows(rows)
    print(f"wrote {len(rows)} anchors to {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
