"""Set-theory and scale analysis of realized patterns."""

from __future__ import annotations

from collections.abc import Iterable

from .cells import Cell
from .progressions import Progression


def pc_set(values: Iterable[int]) -> tuple[int, ...]:
    return tuple(sorted({v % 12 for v in values}))


def cycle_pcs(progression: Progression, cell: Cell) -> tuple[int, ...]:
    """Every pitch class a pattern (started on C) touches over its cycle."""
    P, M = progression.interval, progression.parts
    return pc_set(k * P + x for k in range(M) for x in cell)


def row_prefix(progression: Progression, cell: Cell, length: int = 12) -> list[int]:
    """First ``length`` pitch classes of the pattern line, started on C."""
    out: list[int] = []
    k = 0
    while len(out) < length:
        for x in cell:
            out.append((k * progression.interval + x) % 12)
            if len(out) == length:
                break
        k += 1
    return out


def is_twelve_tone(progression: Progression, cell: Cell) -> bool:
    """True if the first twelve notes are all twelve pitch classes."""
    return len(set(row_prefix(progression, cell))) == 12


def _transpose(pcs: Iterable[int], t: int) -> tuple[int, ...]:
    return tuple(sorted((p + t) % 12 for p in pcs))


def _normal_form(pcs: tuple[int, ...]) -> tuple[int, ...]:
    """Rahn normal form: the most compact rotation, packed to the left."""
    s = sorted(set(pcs))
    n = len(s)
    if n <= 1:
        return tuple(s)
    rotations = [s[i:] + [p + 12 for p in s[:i]] for i in range(n)]

    def key(r: list[int]) -> tuple[int, ...]:
        return tuple(r[j] - r[0] for j in range(n - 1, 0, -1))

    best = min(rotations, key=key)
    return tuple(p % 12 for p in best)


def prime_form(pcs: Iterable[int]) -> tuple[int, ...]:
    s = tuple(sorted({p % 12 for p in pcs}))
    if not s:
        return ()
    candidates = []
    for version in (s, tuple(sorted((-p) % 12 for p in s))):
        nf = _normal_form(version)
        candidates.append(tuple((p - nf[0]) % 12 for p in nf))
    return min(candidates, key=lambda c: tuple(reversed(c)))


def interval_vector(pcs: Iterable[int]) -> tuple[int, ...]:
    s = sorted({p % 12 for p in pcs})
    vec = [0] * 6
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            d = (s[j] - s[i]) % 12
            vec[min(d, 12 - d) - 1] += 1
    return tuple(vec)


def transposition_count(pcs: Iterable[int]) -> int:
    """Distinct transpositions of the set (< 12 means a symmetric scale)."""
    s = tuple(sorted({p % 12 for p in pcs}))
    return len({_transpose(s, t) for t in range(12)})


_NAMED_SETS = {
    "Chromatic scale": range(12),
    "Whole-tone scale": (0, 2, 4, 6, 8, 10),
    "Octatonic (diminished) scale": (0, 1, 3, 4, 6, 7, 9, 10),
    "Augmented (hexatonic) scale": (0, 3, 4, 7, 8, 11),
    "Tritone scale": (0, 1, 4, 6, 7, 10),
    "Two-semitone tritone scale (Messiaen mode 5)": (0, 1, 2, 6, 7, 8),
    "Messiaen mode 3": (0, 2, 3, 4, 6, 7, 8, 10, 11),
    "Messiaen mode 4": (0, 1, 2, 5, 6, 7, 8, 11),
    "Messiaen mode 6": (0, 2, 4, 5, 6, 8, 10, 11),
    "Messiaen mode 7": (0, 1, 2, 3, 5, 6, 7, 8, 9, 11),
    "Diatonic collection": (0, 2, 4, 5, 7, 9, 11),
    "Acoustic (melodic minor) collection": (0, 2, 3, 5, 7, 9, 11),
    "Harmonic minor collection": (0, 2, 3, 5, 7, 8, 11),
    "Pentatonic collection": (0, 2, 4, 7, 9),
    "Diminished seventh chord": (0, 3, 6, 9),
    "Augmented triad": (0, 4, 8),
    "Tritone": (0, 6),
}
_BY_PRIME = {prime_form(v): k for k, v in _NAMED_SETS.items()}


def scale_name(pcs: Iterable[int]) -> str | None:
    return _BY_PRIME.get(prime_form(pcs))


def analyze(progression: Progression, cell: Cell) -> dict:
    pcs = cycle_pcs(progression, cell)
    return {
        "pcs": list(pcs),
        "cardinality": len(pcs),
        "primeForm": list(prime_form(pcs)),
        "intervalVector": list(interval_vector(pcs)),
        "transpositions": transposition_count(pcs),
        "scale": scale_name(pcs),
        "twelveTone": is_twelve_tone(progression, cell),
    }
