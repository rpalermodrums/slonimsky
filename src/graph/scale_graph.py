from .base_graph import BaseGraph
from typing import List
from models import NoteEvent
from mingus.core import notes, intervals
from mingus.core import scales as mingus_scales
import logging

logger = logging.getLogger(__name__)

class ScaleGraphBuilder(BaseGraph):
    def build_scale_graph(self, scale_notes: List[NoteEvent]):
        logger.info(f"Building scale graph with {len(scale_notes)} notes.")
        for note_event in scale_notes:
            logger.debug(f"Adding node: {note_event.note} with octave: {self._extract_octave(note_event.note)} and consonance: {note_event.consonance}")
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
                interval_size = abs(intervals.measure(current_note_event.note, next_note_event.note))
                
                # Allow stepwise motion (minor or major second) and common tones
                if interval_size <= 2 or next_pitch == current_pitch:
                    weight = 10 - interval_size  # Favor smaller intervals
                    logger.debug(f"Adding edge from {current_note_event.note} to {next_note_event.note} with interval: {interval_size} and weight: {weight}")
                    self.add_edge(
                        current_note_event.note,
                        next_note_event.note,
                        interval=interval_size,
                        weight=weight
                    )
        logger.info("Scale graph building completed.")

    def _note_to_pitch(self, note: str) -> int:
        """
        Converts a note (e.g., 'C4') to its MIDI pitch number.
        """
        base_note = note[:-1]
        octave = int(note[-1])
        pitch = notes.note_to_int(base_note) + (octave + 1) * 12  # MIDI octave starts at -1
        logger.debug(f"Converted note {note} to pitch {pitch}.")
        return pitch

    def _extract_octave(self, note: str) -> int:
        """
        Extracts the octave number from a note string.
        """
        octave = int(note[-1])
        logger.debug(f"Extracted octave {octave} from note {note}.")
        return octave