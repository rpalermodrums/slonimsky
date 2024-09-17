from typing import List, Tuple
import networkx as nx
from mingus.core import scales, chords, intervals

from models import NoteEvent, Edge
from scales import Scale

class ScaleGraph:
    def __init__(self, scale: Scale, chord_progression: List[Tuple[str, int]], time_signature: Tuple[int, int] = (4, 4)):
        """
        Initializes a graph representation of a scale over a chord progression.

        :param scale: Scale instance
        :param chord_progression: List of tuples [(chord_symbol, duration_in_beats), ...]
        :param time_signature: Tuple representing the time signature (beats_per_measure, beat_value)
        """
        self.graph = nx.DiGraph()
        self.scale = scale
        self.chord_progression = chord_progression
        self.time_signature = time_signature
        self.beat_types = self._determine_beat_types()
        self.note_events_by_time = {}

    def _determine_beat_types(self) -> List[str]:
        """
        Determines beat types ('strong', 'weak', 'neutral') based on the time signature.

        :return: List of beat types corresponding to each beat.
        """
        beats_per_measure, _ = self.time_signature
        total_beats = sum(duration for _, duration in self.chord_progression)
        beat_types = []
        for beat in range(1, total_beats + 1):
            position_in_measure = (beat - 1) % beats_per_measure
            if position_in_measure == 0:
                beat_types.append('strong')
            elif position_in_measure == beats_per_measure // 2:
                beat_types.append('weak')
            else:
                beat_types.append('neutral')
        return beat_types

    def build_graph(self):
        """
        Builds a graph representing musical ideas and their continuations.
        """
        current_time = 0.0
        for chord_symbol, duration in self.chord_progression:
            chord_notes = chords.from_shorthand(chord_symbol)
            scale_notes = self._get_scale_for_chord(chord_symbol)
            for _ in range(duration):
                current_time += 1.0
                beat_index = int(current_time) - 1
                beat_type = self.beat_types[beat_index]
                available_notes = chord_notes if beat_type == 'strong' else list(set(scale_notes + chord_notes))
                note_events = []
                for note in available_notes:
                    consonance = 'consonant' if note in chord_notes else 'dissonant'
                    note_event = NoteEvent(
                        note=note,
                        time=current_time,
                        chord=chord_symbol,
                        beat_type=beat_type,
                        consonance=consonance
                    )
                    note_events.append(note_event)
                self.note_events_by_time[current_time] = note_events

        times = sorted(self.note_events_by_time.keys())
        for i in range(len(times) - 1):
            time_from = times[i]
            time_to = times[i + 1]
            from_notes = self.note_events_by_time[time_from]
            to_notes = self.note_events_by_time[time_to]
            for from_note_event in from_notes:
                for to_note_event in to_notes:
                    interval = intervals.measure(from_note_event.note, to_note_event.note)
                    weight = self.calculate_weight(interval, from_note_event.consonance, to_note_event.consonance)
                    melodic_rules = {
                        'stepwise_motion': abs(interval) <= 2,
                        'consonant_resolution': from_note_event.consonance == 'dissonant' and to_note_event.consonance == 'consonant'
                    }
                    from_node = (from_note_event.note, from_note_event.time)
                    to_node = (to_note_event.note, to_note_event.time)
                    self.graph.add_edge(
                        from_node,
                        to_node,
                        weight=weight,
                        interval=interval,
                        melodic_rules=melodic_rules
                    )
                    
    def _get_scale_for_chord(self, chord_symbol: str) -> List[str]:
        """
        Determines the appropriate scale for a given chord using Mingus.

        :param chord_symbol: Chord symbol (e.g., 'Dm7')
        :return: List of scale notes
        """
        chord = chords.from_shorthand(chord_symbol)
        chord_root = chord[0]
        chord_type = chords.determine(chord_symbol)[0]

        # Mapping chord types to scales
        scale_mapping = {
            'maj7': scales.Major,
            'm7': scales.Dorian,
            '7': scales.Mixolydian,
            'dim7': scales.Locrian,
            # Extend mapping as needed
        }

        scale_cls = scale_mapping.get(chord_type, scales.Major)  # Default to Major if not found
        selected_scale = scale_cls(chord_root)
        return selected_scale.ascending()

    def calculate_weight(self, interval: int, from_consonance: str, to_consonance: str) -> float:
        """
        Calculates the weight of an edge based on musical criteria.

        :param interval: Interval in semitones between notes.
        :param from_consonance: Consonance of the originating note.
        :param to_consonance: Consonance of the destination note.
        :return: Calculated weight.
        """
        base_weight = 10
        weight = base_weight - abs(interval)
        if from_consonance == 'dissonant' and to_consonance == 'consonant':
            weight += 2  # Resolution bonus
        if abs(interval) > 12:  # Penalize large leaps
            weight -= 5
        return weight