from .base_graph import BaseGraph
from typing import List, Dict
from models import ChordEvent
from mingus.core import chords, keys, progressions, intervals, notes
import logging

logger = logging.getLogger(__name__)

class ChordGraphBuilder(BaseGraph):
    def __init__(self, key: str = 'C'):
        super().__init__()
        self.key = key.upper()
        self.tonic = self.key + 'maj7'
        self.scale = keys.get_notes(self.key, 'major')
        self.functional_roles = self._generate_functional_roles()
        self.circle_of_fifths = self._generate_circle_of_fifths()
        self.modal_interchange = self._generate_modal_interchange()
        self.barry_harris_scales = self._generate_barry_harris_scales()
        self.harmonic_matrices = self._generate_harmonic_matrices()
        logger.info(f"Initialized ChordGraphBuilder with key: {self.key}")

    def build_chord_graph(self, chords: List[ChordEvent]):
        logger.info("Building chord graph...")
        for chord in chords:
            functional_role = self.functional_roles.get(chord.symbol, 'unknown')
            logger.debug(f"Adding node: {chord.symbol} with role: {functional_role}")
            self.add_node(
                chord.symbol,
                type=chord.type,
                functional_role=functional_role,
                degrees=chord.degrees
            )

        # Define harmony transitions based on Circle of Fifths
        for chord in chords:
            possible_transitions = self.circle_of_fifths.get(chord.symbol, [])
            for next_chord in possible_transitions:
                if next_chord in [c.symbol for c in chords]:
                    weight = self._determine_weight(next_chord)
                    logger.debug(f"Adding edge from {chord.symbol} to {next_chord} with weight: {weight}")
                    self.add_edge(
                        chord.symbol,
                        next_chord,
                        resolution=True,
                        weight=weight
                    )

        # Handle Modal Interchange Transitions
        for chord in chords:
            interchange_chords = self.modal_interchange.get(chord.symbol, [])
            for interm_chord in interchange_chords:
                if interm_chord in [c.symbol for c in chords]:
                    logger.debug(f"Adding modal interchange edge from {chord.symbol} to {interm_chord}")
                    self.add_edge(
                        chord.symbol,
                        interm_chord,
                        modal_interchange=True,
                        weight=7
                    )

        # Handle Barry Harris Harmony Transitions
        for chord in chords:
            bh_transitions = self.barry_harris_scales.get(chord.symbol, [])
            for bh_chord in bh_transitions:
                if bh_chord in [c.symbol for c in chords]:
                    logger.debug(f"Adding Barry Harris edge from {chord.symbol} to {bh_chord}")
                    self.add_edge(
                        chord.symbol,
                        bh_chord,
                        barry_harris=True,
                        weight=9
                    )

        # Handle Harmonic Matrices (Ralph Bowen)
        for chord in chords:
            matrix_chords = self.harmonic_matrices.get(chord.symbol, [])
            for matrix_chord in matrix_chords:
                if matrix_chord in [c.symbol for c in chords]:
                    logger.debug(f"Adding harmonic matrix edge from {chord.symbol} to {matrix_chord}")
                    self.add_edge(
                        chord.symbol,
                        matrix_chord,
                        harmonic_matrix=True,
                        weight=8
                    )

        # Handle Chord Inversions
        for chord in chords:
            if '/' in chord.symbol:
                root, bass = chord.symbol.split('/')
                logger.debug(f"Adding inversion edge from {bass} to {chord.symbol}")
                self.add_edge(
                    bass,
                    chord.symbol,
                    inversion=True,
                    weight=10
                )

    def _generate_functional_roles(self) -> Dict[str, str]:
        """
        Generate functional roles for diatonic chords based on the current key.
        """
        roles = {}
        diatonic_chords = keys.get_chords(self.key, 'major')
        roman_numerals = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
        for i, chord_notes in enumerate(diatonic_chords):
            numeral = roman_numerals[i]
            chord_name = chords.determine(chord_notes)
            if chord_name:
                chord_symbol = chord_name[0]
                if numeral == 'I':
                    role = 'tonic'
                elif numeral == 'V':
                    role = 'dominant'
                elif numeral == 'IV':
                    role = 'subdominant'
                else:
                    role = 'pre-dominant'
                roles[chord_symbol] = role
                logger.debug(f"Assigned role '{role}' to chord '{chord_symbol}'")
        return roles

    def _generate_circle_of_fifths(self) -> Dict[str, List[str]]:
        """
        Generate the Circle of Fifths transitions based on the current key.
        """
        circle = {}
        all_chords = chords.major_triad_shorthand.keys()
        for chord_symbol in all_chords:
            # Find the chord a perfect fifth above and below
            fifth_above = notes.int_to_note(
                (notes.note_to_int(chord_symbol) + 7) % 12
            ) + 'maj7'
            fifth_below = notes.int_to_note(
                (notes.note_to_int(chord_symbol) + 5) % 12
            ) + 'maj7'
            circle[chord_symbol] = [fifth_above, fifth_below]
            logger.debug(f"Circle of Fifths for {chord_symbol}: {circle[chord_symbol]}")
        return circle

    def _generate_modal_interchange(self) -> Dict[str, List[str]]:
        """
        Generate modal interchange chords based on parallel modes.
        """
        interchange = {}
        mode_names = ['dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian']
        for mode in mode_names:
            modal_scale = keys.get_notes(self.key, mode)
            modal_chords = chords.triads(modal_scale)
            for chord_notes in modal_chords:
                chord_name = chords.determine(chord_notes)
                if chord_name:
                    chord_symbol = chord_name[0]
                    interchange.setdefault(chord_symbol, []).append(chord_symbol)
                    logger.debug(f"Modal interchange for {chord_symbol}: {interchange[chord_symbol]}")
        return interchange

    def _generate_barry_harris_scales(self) -> Dict[str, List[str]]:
        """
        Generate chords based on Barry Harris's harmonic concepts.
        """
        bh_scales = {}
        bh_scale_notes = self._barry_harris_scale()
        bh_chords = []
        for i in range(len(bh_scale_notes) - 2):
            chord_notes = [bh_scale_notes[i], bh_scale_notes[i+1], bh_scale_notes[i+2]]
            bh_chords.append(chord_notes)
        for chord_notes in bh_chords:
            chord_name = chords.determine(chord_notes)
            if chord_name:
                chord_symbol = chord_name[0]
                bh_scales.setdefault(chord_symbol, []).append(chord_symbol)
                logger.debug(f"Barry Harris scale for {chord_symbol}: {bh_scales[chord_symbol]}")
        return bh_scales

    def _barry_harris_scale(self) -> List[str]:
        """
        Generate the Barry Harris 6th diminished scale for the current key.
        """
        major_scale = keys.get_notes(self.key, 'major')
        diminished_note = notes.int_to_note(
            (notes.note_to_int(major_scale[5]) + 1) % 12
        )
        bh_scale = major_scale[:5] + [diminished_note] + major_scale[5:]
        logger.debug(f"Generated Barry Harris scale for key {self.key}: {bh_scale}")
        return bh_scale

    def _generate_harmonic_matrices(self) -> Dict[str, List[str]]:
        """
        Generate chords based on Ralph Bowen's harmonic matrices.
        """
        matrices = {}
        # Implementing tritone substitutions as an example
        for chord_symbol in self.functional_roles.keys():
            root_note = chord_symbol[:-3]  # Removing chord type (e.g., 'maj', 'min')
            tritone_note = intervals.get_tone_from_semitones(root_note, 6)
            tritone_chord = tritone_note + chord_symbol[-3:]
            matrices.setdefault(chord_symbol, []).append(tritone_chord)
            logger.debug(f"Generated harmonic matrix for {chord_symbol}: {matrices[chord_symbol]}")
        return matrices

    def _determine_weight(self, next_chord: str) -> int:
        """
        Determine the weight of transitioning to the next chord based on its functional role.
        """
        role_weights = {
            'tonic': 15,
            'dominant': 12,
            'subdominant': 10,
            'pre-dominant': 8,
            'unknown': 5
        }
        role = self.functional_roles.get(next_chord, 'unknown')
        weight = role_weights.get(role, 5)
        logger.debug(f"Determined weight for transition to {next_chord}: {weight}")
        return weight