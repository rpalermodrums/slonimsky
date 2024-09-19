# src/graph/harmony_graph.py
from .base_graph import BaseGraph
from typing import List
from models import ChordEvent

class HarmonyGraphBuilder(BaseGraph):
    FUNCTIONAL_ROLES = {
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

    CIRCLE_OF_FIFTHS = {
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

    MODAL_INTERCHANGE = {
        'Cmaj7': ['Cmin7', 'C7'],
        'G7': ['Gm7', 'Gmaj7'],
        # Add more mappings as needed
    }

    def build_harmony_graph(self, chords: List[ChordEvent]):
        for chord in chords:
            functional_role = self.FUNCTIONAL_ROLES.get(chord.symbol, 'unknown')
            self.add_node(
                chord.symbol,
                type=chord.type,
                functional_role=functional_role,
                degrees=chord.degrees
            )
        
        # Define harmony transitions based on Circle of Fifths
        for chord in chords:
            possible_transitions = self.CIRCLE_OF_FIFTHS.get(chord.symbol, [])
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

    def _determine_weight(self, next_chord: str) -> int:
        """
        Determines the weight of transitioning to the next chord based on its functional role.
        """
        role_weights = {
            'tonic': 15,
            'dominant': 12,
            'secondary_dominant': 12,
            'subdominant': 10,
            'unknown': 8
        }
        role = self.FUNCTIONAL_ROLES.get(next_chord, 'unknown')
        return role_weights.get(role, 8)