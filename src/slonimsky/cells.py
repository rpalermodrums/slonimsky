"""Cells: the repeating melodic unit of a Slonimsky pattern.

A cell is a tuple of semitone offsets measured from the current principal
tone, always starting with 0. The next principal tone sits at +P and is
*not* part of the cell. Each added note gets a role:

* ``I`` infrapolation: below the current principal tone   (offset < 0)
* ``N`` interpolation: between the two principal tones    (0 < offset < P)
* ``U`` ultrapolation: above the next principal tone      (offset > P)

Slonimsky's section names come straight from the roles in the order they
occur, e.g. ``C  B  D  A -> E`` in the Ditone progression is
``(0, -1, 2, 9)`` = infra, inter, ultra = "Infra-Inter-Ultrapolation".
"""

from __future__ import annotations

from dataclasses import dataclass

from .progressions import number_word

INFRA, INTER, ULTRA = "I", "N", "U"
ROLE_PREFIX = {INFRA: "Infra", INTER: "Inter", ULTRA: "Ultra"}
ROLE_WORD = {INFRA: "infrapolation", INTER: "interpolation", ULTRA: "ultrapolation"}

Cell = tuple[int, ...]


class CellError(ValueError):
    pass


def role_of(offset: int, interval: int) -> str:
    if offset < 0:
        return INFRA
    if 0 < offset < interval:
        return INTER
    if offset > interval:
        return ULTRA
    raise CellError(f"offset {offset} coincides with a principal tone")


def roles_of(cell: Cell, interval: int) -> tuple[str, ...]:
    validate(cell, interval)
    return tuple(role_of(x, interval) for x in cell[1:])


def validate(cell: Cell, interval: int) -> None:
    if not cell or cell[0] != 0:
        raise CellError("a cell must start with offset 0 (the principal tone)")
    for x in cell[1:]:
        if x == 0 or x == interval:
            raise CellError(f"offset {x} coincides with a principal tone")


def _runs(roles: tuple[str, ...]) -> list[tuple[str, int]]:
    runs: list[tuple[str, int]] = []
    for r in roles:
        if runs and runs[-1][0] == r:
            runs[-1] = (r, runs[-1][1] + 1)
        else:
            runs.append((r, 1))
    return runs


def section_label(roles: tuple[str, ...]) -> str:
    """Slonimsky-style heading for a role sequence."""
    if not roles:
        return "Principal Tones"
    runs = _runs(roles)
    if len(runs) == 1:
        role, n = runs[0]
        noun = "Note" if n == 1 else "Notes"
        return f"{ROLE_WORD[role].capitalize()} of {number_word(n)} {noun}"
    words = [ROLE_PREFIX[r] for r, _ in runs]
    label = "-".join(words[:-1]) + "-" + ROLE_WORD[runs[-1][0]].capitalize()
    if any(n > 1 for _, n in runs):
        label += " (" + " + ".join(str(n) for _, n in runs) + " notes)"
    return label


def section_key(roles: tuple[str, ...]) -> str:
    if not roles:
        return "principal"
    runs = _runs(roles)
    if len(runs) == 1:
        role, n = runs[0]
        return f"{ROLE_WORD[role]}-{n}"
    parts = []
    for r, n in runs:
        p = ROLE_PREFIX[r].lower()
        parts.append(p if n == 1 else f"{p}{n}")
    return "-".join(parts)


def pcs_of(cell: Cell) -> tuple[int, ...]:
    return tuple(x % 12 for x in cell)


def has_pc_repeat(cell: Cell, interval: int) -> bool:
    """True if a pitch class occurs twice among the cell and the next principal."""
    full = [x % 12 for x in cell] + [interval % 12]
    return len(set(full)) != len(full)


@dataclass(frozen=True)
class Classification:
    roles: tuple[str, ...]
    key: str
    label: str

    def to_dict(self) -> dict:
        return {"roles": list(self.roles), "key": self.key, "label": self.label}


def classify(cell: Cell, interval: int) -> Classification:
    roles = roles_of(cell, interval)
    return Classification(roles, section_key(roles), section_label(roles))


def describe(cell: Cell, interval: int) -> list[dict]:
    """Per-note derivation: role and distance from the nearest principal tone."""
    out = [{"offset": 0, "role": "P", "text": "principal tone"}]
    for x in cell[1:]:
        r = role_of(x, interval)
        if r == INFRA:
            text = f"{-x} below the principal tone"
        elif r == INTER:
            text = f"{x} above the principal tone"
        else:
            text = f"{x - interval} above the next principal tone"
        out.append({"offset": x, "role": r, "text": text})
    return out


def parse_cell(text: str) -> Cell:
    """Parse '0,-1,2,9' or '-1 2 9' (leading 0 optional) into a cell."""
    items = [t for t in text.replace(",", " ").split() if t]
    values = tuple(int(t) for t in items)
    if not values or values[0] != 0:
        values = (0,) + values
    return values
