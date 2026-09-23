"""Turn a cell into playable notes.

The cell is sequenced on every principal tone of one full cycle (M
repetitions spanning N octaves), then the line lands on the final
principal tone, as in the book. Mirrored in ``web/engine.js``; keep the
two in step (tests/test_js_parity.py checks them).
"""

from __future__ import annotations

from dataclasses import dataclass

from .cells import Cell, role_of
from .pitch import midi_name, prefers_sharps
from .progressions import Progression

DIRECTIONS = ("up", "down", "updown")


@dataclass(frozen=True)
class Note:
    midi: int
    role: str  # "P" principal, or I / N / U
    group: int  # which repetition of the cell (the final tone gets M)

    def to_dict(self, sharps: bool = True) -> dict:
        return {"midi": self.midi, "role": self.role, "group": self.group,
                "name": midi_name(self.midi, sharps)}


def default_fold(progression: Progression) -> int | None:
    """Multi-octave cycles are folded into two octaves unless asked otherwise."""
    return 2 if progression.octaves > 2 else None


def realize(
    progression: Progression,
    cell: Cell,
    root: int = 60,
    direction: str = "up",
    fold: int | None | str = "auto",
) -> list[Note]:
    """Realize ``cell`` over one full cycle of ``progression``.

    direction: "up" ascends; "down" mirrors the whole pattern (inversion, the
    principal tones descend); "updown" goes up and then retraces its steps.
    fold: keep principal tones within ``fold`` octaves of the root by moving
    whole cells down an octave (for the 5-, 7- and 11-octave cycles).
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    if fold == "auto":
        fold = default_fold(progression)
    sign = -1 if direction == "down" else 1
    P = progression.interval
    M = progression.parts
    notes: list[Note] = []
    for k in range(M + 1):
        base = k * P
        if fold:
            base = _fold(base, fold)
        offsets = cell if k < M else (0,)
        for x in offsets:
            role = "P" if x == 0 else role_of(x, P)
            notes.append(Note(root + sign * (base + x), role, k))
    if direction == "updown":
        notes = notes + list(reversed(notes[:-1]))
    return notes


def _fold(base: int, octaves: int) -> int:
    span = 12 * octaves
    return base % span if base >= span else base


def spelling_sharps(progression: Progression, preference: str = "auto") -> bool:
    if preference == "sharps":
        return True
    if preference == "flats":
        return False
    return prefers_sharps(progression.interval)
