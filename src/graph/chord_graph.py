# src/graph/chord_graph.py
from .base_graph import BaseGraph
from typing import List
from models import ChordEvent

class ChordGraphBuilder(BaseGraph):
    # Define Modal Interchange mappings
    MODAL_INTERCHANGE = {
        'Cmaj7': ['Cmin7', 'C7'],
        'G7': ['Gm7', 'Gmaj7'],
        # Add more mappings as needed
    }

    def build_chord_graph(self, chords: List[ChordEvent], scale_graph: BaseGraph):
        for chord in chords:
            functional_role = self._assign_functional_role(chord.symbol)
            self.add_node(
                chord.symbol,
                type=chord.type,
                functional_role=functional_role,
                degrees=chord.degrees
            )
        
        # Define Harmony Transitions based on Functional Harmony and Circle of Fifths
        for chord in chords:
            possible_transitions = self._get_circle_of_fifths_transitions(chord.symbol)
            for next_chord in possible_transitions:
                if next_chord in [c.symbol for c in chords]:
                    weight = self._determine_weight(next_chord)
                    self.add_edge(
                        chord.symbol,
                        next_chord,
                        resolution=True,
                        weight=weight
                    )
        
        # Handle Modal Interchange Transitions
        for chord in chords:
            interchange_chords = self.MODAL_INTERCHANGE.get(chord.symbol, [])
            for interm_chord in interchange_chords:
                if interm_chord in [c.symbol for c in chords]:
                    self.add_edge(
                        chord.symbol,
                        interm_chord,
                        modal_interchange=True,
                        weight=7
                    )
        
        # Handle Chord Inversions
        for chord in chords:
            if '/' in chord.symbol:
                root, bass = chord.symbol.split('/')
                self.add_edge(
                    bass,
                    chord.symbol,
                    inversion=True,
                    weight=9
                )

    def _assign_functional_role(self, chord_symbol: str) -> str:
        """
        Assigns a functional role to a chord based on its symbol.
        """
        functional_roles = {
            'Cmaj7': 'tonic',
            'G7': 'dominant',
            'D7': 'secondary_dominant',
            'A7': 'secondary_dominant',
            'E7': 'secondary_dominant',
            'B7': 'secondary_dominant',
            'Fmaj7': 'subdominant',
            'Bbmaj7': 'subdominant',
            'Ebmaj7': 'subdominant',
            'Abmaj7': 'subdominant',
            'Dbmaj7': 'subdominant',
            'Gbmaj7': 'subdominant',
            'Cbmaj7': 'subdominant',
            'Fbmaj7': 'subdominant',
        }
        return functional_roles.get(chord_symbol, 'unknown')

    def _get_circle_of_fifths_transitions(self, chord_symbol: str) -> List[str]:
        """
        Returns a list of chord symbols that are a fifth away from the given chord.
        """
        circle_of_fifths = {
            'Cmaj7': ['G7', 'Fmaj7'],
            'G7': ['Cmaj7', 'D7'],
            'D7': ['G7', 'A7'],
            'A7': ['D7', 'E7'],
            'E7': ['A7', 'B7'],
            'B7': ['E7', 'Cmaj7'],
            'Fmaj7': ['Bbmaj7', 'Cmaj7'],
            'Bbmaj7': ['Ebmaj7', 'Fmaj7'],
            'Ebmaj7': ['Abmaj7', 'Bbmaj7'],
            'Abmaj7': ['Dbmaj7', 'Ebmaj7'],
            'Dbmaj7': ['Gbmaj7', 'Abmaj7'],
            'Gbmaj7': ['Cbmaj7', 'Dbmaj7'],
            'Cbmaj7': ['Fbmaj7', 'Gbmaj7'],
            'Fbmaj7': ['Bbmaj7', 'Cbmaj7'],
        }
        return circle_of_fifths.get(chord_symbol, [])

    def _determine_weight(self, next_chord: str) -> int:
        """
        Determines the weight of the transition based on the functional role of the next chord.
        """
        functional_roles = {
            'tonic': 15,
            'dominant': 12,
            'secondary_dominant': 12,
            'subdominant': 10,
            'unknown': 8
        }
        role = self._assign_functional_role(next_chord)
        return functional_roles.get(role, 8)