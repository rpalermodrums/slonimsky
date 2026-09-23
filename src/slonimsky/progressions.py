"""The twelve interval progressions (chapters) of the Thesaurus.

Every chapter is an *equal division of N octaves into M parts*: the
principal interval P satisfies ``N * 12 == M * P``. Repeating P from a
starting tone yields the principal tones; after M steps the line has
climbed exactly N octaves and returns to the starting pitch class.

Chapter order and names follow the book. Pattern-number ranges are only
filled in where a source states them (see ``data/anchors.csv`` and
docs/FINDINGS.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

_NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
    7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve",
}


def number_word(n: int) -> str:
    return _NUMBER_WORDS.get(n, str(n))


@dataclass(frozen=True)
class Progression:
    key: str
    name: str
    interval: int  # principal interval P, in semitones
    order: int  # chapter position in the book
    book_range: tuple[int, int] | None = None

    @property
    def octaves(self) -> int:
        """N: how many octaves one full cycle spans."""
        return self.interval // gcd(self.interval, 12)

    @property
    def parts(self) -> int:
        """M: how many principal intervals make one full cycle."""
        return 12 // gcd(self.interval, 12)

    @property
    def description(self) -> str:
        n = self.octaves
        octave_word = "Octave" if n == 1 else "Octaves"
        return (
            f"Equal Division of {number_word(n)} {octave_word} "
            f"into {number_word(self.parts)} Parts"
        )

    @property
    def title(self) -> str:
        return f"{self.name} Progression"

    def principal_pcs(self) -> frozenset[int]:
        """Pitch classes touched by the principal-tone cycle starting on C."""
        return frozenset((k * self.interval) % 12 for k in range(self.parts))

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "title": self.title,
            "interval": self.interval,
            "octaves": self.octaves,
            "parts": self.parts,
            "order": self.order,
            "description": self.description,
            "bookRange": list(self.book_range) if self.book_range else None,
        }


PROGRESSIONS: tuple[Progression, ...] = (
    Progression("tritone", "Tritone", 6, 1, (1, 180)),
    Progression("ditone", "Ditone", 4, 2, (181, 391)),
    Progression("sesquitone", "Sesquitone", 3, 3, (392, 568)),
    Progression("whole-tone", "Whole-Tone", 2, 4),
    Progression("semitone", "Semitone", 1, 5),
    Progression("quadritone", "Quadritone", 8, 6),
    Progression("sesquiquadritone", "Sesquiquadritone", 9, 7),
    Progression("quinquetone", "Quinquetone", 10, 8),
    Progression("diatessaron", "Diatessaron", 5, 9),
    Progression("septitone", "Septitone", 14, 10),
    Progression("diapente", "Diapente", 7, 11),
    Progression("sesquiquinquetone", "Sesquiquinquetone", 11, 12),
)

_BY_KEY = {p.key: p for p in PROGRESSIONS}
_ALIASES = {
    "whole tone": "whole-tone", "wholetone": "whole-tone", "chromatic": "semitone",
    "fourth": "diatessaron", "fourths": "diatessaron", "fifth": "diapente",
    "fifths": "diapente",
}


def get_progression(key: str | int) -> Progression:
    """Look a progression up by key, name, alias or principal interval."""
    if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
        interval = int(key)
        for p in PROGRESSIONS:
            if p.interval == interval:
                return p
        raise KeyError(f"no progression with interval {interval}")
    k = key.strip().lower().replace("_", "-")
    k = _ALIASES.get(k, k)
    if k.endswith(" progression"):
        k = k[: -len(" progression")]
    if k in _BY_KEY:
        return _BY_KEY[k]
    for p in PROGRESSIONS:
        if p.name.lower() == k:
            return p
    raise KeyError(f"unknown progression: {key!r}")
