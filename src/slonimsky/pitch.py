"""Pitch helpers: pitch classes, spelling, MIDI numbers.

Spelling is deliberately simple and deterministic (the JS UI mirrors it):
every pitch class gets one spelling for the whole pattern, chosen from a
sharp table or a flat table.
"""

from __future__ import annotations

SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")

# Principal intervals whose cycles read more naturally with sharps.
# Everything else defaults to flats (sesquitone C Eb Gb A, fourths C F Bb ...).
SHARP_PREFERRED_INTERVALS = frozenset({1, 2, 4, 6, 7, 9, 14})

_LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def pc(value: int) -> int:
    """Pitch class of an integer semitone value."""
    return value % 12


def prefers_sharps(interval: int) -> bool:
    return interval in SHARP_PREFERRED_INTERVALS


def pc_name(pitch_class: int, sharps: bool = True) -> str:
    return (SHARP_NAMES if sharps else FLAT_NAMES)[pitch_class % 12]


def midi_name(midi: int, sharps: bool = True) -> str:
    """Scientific pitch name, middle C (60) = C4."""
    return f"{pc_name(midi, sharps)}{midi // 12 - 1}"


def parse_pc(name: str) -> int:
    """Parse a note name like 'C', 'F#', 'Bb', 'Ebb', 'C♯' into a pitch class."""
    s = name.strip().replace("♯", "#").replace("♭", "b")
    if not s:
        raise ValueError("empty note name")
    letter = s[0].upper()
    if letter not in _LETTER_PC:
        raise ValueError(f"not a note name: {name!r}")
    value = _LETTER_PC[letter]
    for ch in s[1:]:
        if ch == "#":
            value += 1
        elif ch == "b":
            value -= 1
        elif ch.isdigit() or ch == "-":
            break
        else:
            raise ValueError(f"not a note name: {name!r}")
    return value % 12


def parse_midi(name: str) -> int:
    """Parse 'C4', 'F#3', 'Bb5' or a bare integer into a MIDI number."""
    s = name.strip()
    if s.lstrip("-").isdigit():
        return int(s)
    i = 1
    while i < len(s) and s[i] in "#b♯♭":
        i += 1
    octave = int(s[i:]) if s[i:] else 4
    return parse_pc(s[:i]) + 12 * (octave + 1)
