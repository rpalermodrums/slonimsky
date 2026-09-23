"""ABC notation export (rendered in the UI by abcjs).

Each repetition of the cell gets its own bar, so the sequence structure is
visible on the page. Accidentals are written explicitly and cancelled with
naturals within a bar, so the output reads correctly in any renderer.
Mirrored in ``web/engine.js``.
"""

from __future__ import annotations

from .realize import Note

_SHARP = ("C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B")
_FLAT = ("C", "_D", "D", "_E", "E", "F", "_G", "G", "_A", "A", "_B", "B")


def _abc_pitch(midi: int, sharps: bool, bar_state: dict) -> str:
    token = (_SHARP if sharps else _FLAT)[midi % 12]
    acc, letter = (token[0], token[1]) if len(token) == 2 else ("=", token)
    octave = midi // 12 - 1  # C4 = middle C
    key = (letter, octave)
    shown = "" if bar_state.get(key, "=") == acc else acc
    bar_state[key] = acc
    if octave >= 5:
        body = letter.lower() + "'" * (octave - 5)
    else:
        body = letter + "," * (4 - octave)
    return shown + body


def to_abc(
    notes: list[Note],
    title: str = "",
    sharps: bool = True,
    bars_per_line: int = 4,
    unit: str = "1/8",
) -> str:
    midis = sorted(n.midi for n in notes)
    median = midis[len(midis) // 2] if midis else 60
    clef = "bass" if median < 57 else "treble"
    header = ["X:1"]
    if title:
        header.append(f"T:{title}")
    header += ["M:none", f"L:{unit}", f"K:C clef={clef}"]
    bars: list[str] = []
    current: list[str] = []
    state: dict = {}
    group = notes[0].group if notes else 0
    for n in notes:
        if n.group != group:
            bars.append("".join(current))
            current, state, group = [], {}, n.group
        current.append(_abc_pitch(n.midi, sharps, state))
    if current:
        bars.append("".join(current))
    lines = []
    for i in range(0, len(bars), bars_per_line):
        chunk = bars[i : i + bars_per_line]
        end = " |]" if i + bars_per_line >= len(bars) else " |"
        lines.append(" | ".join(chunk) + end)
    return "\n".join(header + lines) + "\n"
