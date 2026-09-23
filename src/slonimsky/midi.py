"""Minimal Standard MIDI File writer (format 0, one track)."""

from __future__ import annotations

import struct

from .realize import Note

TICKS_PER_QUARTER = 480


def _vlq(value: int) -> bytes:
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def to_midi(
    notes: list[Note],
    tempo_bpm: float = 100.0,
    note_value: float = 0.5,  # in quarter notes: 0.5 = eighth notes
    velocity: int = 88,
    accent: int = 16,
    program: int = 0,
    gate: float = 0.9,
) -> bytes:
    step = int(TICKS_PER_QUARTER * note_value)
    on_len = max(1, int(step * gate))
    track = bytearray()
    uspq = int(round(60_000_000 / tempo_bpm))
    track += _vlq(0) + b"\xff\x51\x03" + uspq.to_bytes(3, "big")
    track += _vlq(0) + bytes([0xC0, program & 0x7F])
    pending = 0
    for n in notes:
        v = min(127, velocity + (accent if n.role == "P" else 0))
        track += _vlq(pending) + bytes([0x90, n.midi & 0x7F, v])
        track += _vlq(on_len) + bytes([0x80, n.midi & 0x7F, 0])
        pending = step - on_len
    track += _vlq(pending) + b"\xff\x2f\x00"
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_QUARTER)
    return header + b"MTrk" + struct.pack(">I", len(track)) + bytes(track)
