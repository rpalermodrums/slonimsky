# src/graph/scale_graph.py
from .base_graph import BaseGraph
from typing import List
from models import NoteEvent
from mingus.core import intervals

class ScaleGraphBuilder(BaseGraph):
    def build_scale_graph(self, scale_notes: List[NoteEvent]):
        for note_event in scale_notes:
            self.add_node(
                note_event.note,
                octave=self._extract_octave(note_event.note),
                consonance=note_event.consonance
            )
        
        # Define allowed transitions based on stepwise motion and voice leading
        for current_note_event in scale_notes:
            current_pitch = self._note_to_pitch(current_note_event.note)
            for next_note_event in scale_notes:
                if current_note_event == next_note_event:
                    continue
                next_pitch = self._note_to_pitch(next_note_event.note)
                interval_size = abs(next_pitch - current_pitch)
                
                # Allow stepwise motion (minor or major second) and common tones
                if interval_size <= 2 or next_pitch == current_pitch:
                    weight = 10 - interval_size  # Favor smaller intervals
                    self.add_edge(
                        current_note_event.note,
                        next_note_event.note,
                        interval=interval_size,
                        weight=weight
                    )

    def _note_to_pitch(self, note: str) -> int:
        """
        Converts a note (e.g., 'C4') to its MIDI pitch number.
        """
        from mingus.core import notes
        base_note = note[:-1]
        octave = int(note[-1])
        return notes.note_to_int(base_note) + (octave + 1) * 12  # MIDI octave starts at -1

    def _extract_octave(self, note: str) -> int:
        """
        Extracts the octave number from a note string.
        """
        return int(note[-1])