from typing import List, Dict
import logging

from mingus.core import chords, keys, progressions, intervals

from models import NoteEvent, ChordEvent, RhythmEvent, TimbreEvent, OtherEvent
from .base_graph import BaseGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def degrees_to_roman(degree):
    return progressions.int_to_roman(degree)

class HarmonyGraphBuilder(BaseGraph):
    def __init__(self, key: str = 'C'):
        super().__init__()
        self.key = key.upper()
        self.previous_note = None
        self.threshold_time = 5  # example threshold in seconds
        self.tonic = self.key + 'maj'
        self.scale = keys.get_scale(self.key, 'major').ascending()
        self.functional_roles = self._generate_functional_roles()
        self.circle_of_fifths = self._generate_circle_of_fifths()
        self.modal_interchange = self._generate_modal_interchange()
        logger.info(f'HarmonyGraphBuilder initialized with key: {self.key}')

    def _generate_functional_roles(self) -> Dict[str, str]:
        """
        Generate functional roles for diatonic and non-diatonic chords based on the current key.
        """
        roles = {}
        diatonic_chords = keys.get_chords(self.key, 'major')
        for i, chord in enumerate(diatonic_chords, 1):
            if i == 1:
                roles[chord] = 'tonic'
            elif i == 5:
                roles[chord] = 'dominant'
            elif i == 4:
                roles[chord] = 'subdominant'
            else:
                roles[chord] = f'stone_{i}'
        
        # Secondary Dominants
        for degree in [2, 3, 6]:
            secondary_dom = progressions.secondary_dominant(self.key, degree)
            if secondary_dom:
                roles[secondary_dom] = f'secondary_dominant_of_{degrees_to_roman(degree)}'
                logger.debug(f'Added secondary dominant: {secondary_dom}')
        
        # Modal Interchange Chords
        modes = ['mixolydian', 'dorian', 'phrygian', 'lydian', 'aeolian', 'locrian']
        for mode in modes:
            modal_chords = keys.get_chords(self.key, mode)
            for chord in modal_chords:
                if chord not in roles:
                    roles[chord] = f'modal_{mode}'
                    logger.debug(f'Added modal interchange chord: {chord} for mode: {mode}')
        return roles

    def _generate_circle_of_fifths(self) -> Dict[str, List[str]]:
        """
        Generate the Circle of Fifths transitions based on the current key.
        """
        circle = {}
        diatonic_chords = keys.get_chords(self.key, 'major')
        for i, chord in enumerate(diatonic_chords, 1):
            dominant = progressions.next_chord(chord, 'V')
            subdominant = progressions.next_chord(chord, 'IV')
            secondary_dominants = progressions.secondary_dominant(self.key, i)
            transitions = [dominant, subdominant] + secondary_dominants
            circle[chord] = transitions
            logger.debug(f'Circle of Fifths for {chord}: {transitions}')
        return circle

    def _generate_modal_interchange(self) -> Dict[str, List[str]]:
        """
        Generate modal interchange chords based on the current key using all common modes.
        """
        interchange = {}
        diatonic_chords = keys.get_chords(self.key, 'major')
        common_modes = ['dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian']
        for chord in diatonic_chords:
            interchange_chords = []
            for mode in common_modes:
                mode_chords = keys.get_chords(self.key, mode)
                interchange_chords.extend([c for c in mode_chords if c not in diatonic_chords])
            interchange[chord] = list(set(interchange_chords))  # Remove duplicates
            logger.debug(f'Modal interchange for {chord}: {interchange[chord]}')
        return interchange

    def _identify_mode(self, chord: str) -> str:
        """
        Identify the mode for modal interchange based on the chord type.
        """
        from mingus.core import chords as mingus_chords

        # Parse the chord to get its qualities
        chord_notes = mingus_chords.from_shorthand(chord)
        chord_info = mingus_chords.determine(chord_notes)

        # Define a comprehensive mapping from chord types to modes
        chord_to_mode_mapping = {
            'major': 'ionian',
            'minor': 'aeolian',
            'major seventh': 'lydian',
            'minor seventh': 'dorian',
            'dominant seventh': 'mixolydian',
            'half-diminished seventh': 'locrian',
            'diminished seventh': 'locrian',
            'augmented': 'lydian',
            'suspended second': 'ionian',
            'suspended fourth': 'phrygian',
            'added ninth': 'mixolydian',
            'sixth': 'aeolian',
            'ninth': 'dorian',
            'minor major seventh': 'altered',
            'major sixth': 'lydian',
            'minor sixth': 'dorian',
            'augmented seventh': 'superlocrian',
            # Add more mappings as needed
        }

        # Iterate through determined chord types and map to mode
        for chord_type in chord_info:
            mode = chord_to_mode_mapping.get(chord_type.lower())
            if mode:
                logger.debug(f'Identified mode {mode} for chord type {chord_type}')
                return mode

        logger.warning(f'No mode identified for chord: {chord}')
        return ''

    def build_harmony_graph(self, events: List):
        """
        Build the harmony graph incrementally based on a list of musical events.
        """
        logger.info('Building harmony graph...')
        for event in events:
            if isinstance(event, ChordEvent):
                self._process_chord_event(event, events)
            elif isinstance(event, NoteEvent):
                self._process_note_event(event)
            elif isinstance(event, RhythmEvent):
                self._process_rhythm_event(event)
            elif isinstance(event, TimbreEvent):
                self._process_timbre_event(event)
            elif isinstance(event, OtherEvent):
                self._process_other_event(event)
            # Handle other event types exhaustively

        self._detect_motifs(events)

    def _process_chord_event(self, chord: ChordEvent, all_events: List):
        functional_role = self.functional_roles.get(chord.symbol, 'unknown')
        self.add_node(
            chord.symbol,
            type='chord',
            functional_role=functional_role,
            degrees=chord.degrees
        )
        logger.info(f'Processed chord event: {chord.symbol} with role: {functional_role}')
        
        # Define harmony transitions based on Circle of Fifths
        possible_transitions = self.circle_of_fifths.get(chord.symbol, [])
        for next_chord in possible_transitions:
            if next_chord in [c.symbol for c in all_events if isinstance(c, ChordEvent)]:
                weight = self._determine_weight(next_chord)
                self.add_edge(
                    chord.symbol,
                    next_chord,
                    resolution=True,
                    weight=weight
                )
                logger.debug(f'Added edge from {chord.symbol} to {next_chord} with weight: {weight}')
        
        # Handle Modal Interchange Transitions
        interchange_chords = self.modal_interchange.get(chord.symbol, [])
        for interm_chord in interchange_chords:
            if interm_chord in [c.symbol for c in all_events if isinstance(c, ChordEvent)]:
                self.add_edge(
                    chord.symbol,
                    interm_chord,
                    modal_interchange=True,
                    weight=7
                )
                logger.debug(f'Added modal interchange edge from {chord.symbol} to {interm_chord}')
        
        # Handle Chord Inversions
        if '/' in chord.symbol:
            root, bass = chord.symbol.split('/')
            self.add_edge(
                bass,
                chord.symbol,
                inversion=True,
                weight=9
            )
            logger.debug(f'Added inversion edge from {bass} to {chord.symbol}')

    def _process_note_event(self, note: NoteEvent):
        """
        Process individual note events and add them to the graph.
        """
        self.add_node(
            note.pitch,
            type='note',
            duration=note.duration,
            intensity=note.intensity
        )
        logger.info(f'Processed note event: {note.pitch} with duration: {note.duration} and intensity: {note.intensity}')
        
        # Connect notes based on voice leading and melodic patterns
        if self.previous_note:
            voice_leading_weight = self._calculate_voice_leading_weight(self.previous_note.pitch, note.pitch)
            self.add_edge(
                self.previous_note.pitch,
                note.pitch,
                voice_leading=True,
                weight=voice_leading_weight
            )
            logger.debug(f'Added voice leading edge from {self.previous_note.pitch} to {note.pitch} with weight: {voice_leading_weight}')
        self.previous_note = note

    def _calculate_voice_leading_weight(self, from_pitch: str, to_pitch: str) -> int:
        """
        Calculate the weight of transitioning from one pitch to another based on voice leading principles.
        """
        interval = self._calculate_interval(from_pitch, to_pitch)
        if interval in ['unison', 'minor third', 'major third', 'perfect fifth', 'octave']:
            return 10  # Strong voice leading
        elif interval in ['minor second', 'major second', 'perfect fourth', 'minor sixth', 'major sixth', 'minor seventh', 'major seventh']:
            return 5   # Weaker voice leading
        else:
            return 3   # Dissonant intervals

    def _calculate_interval(self, from_pitch: str, to_pitch: str) -> str:
        """
        Determine the interval name between two pitches.
        """
        # Simplified interval calculation using Mingus
        try:
            interval_number = intervals.distance(from_pitch, to_pitch)
            interval_name = intervals.int_to_note_name(interval_number)
            return interval_name
        except Exception as e:
            logger.error(f'Error calculating interval from {from_pitch} to {to_pitch}: {e}')
            return 'unknown'

    def _process_rhythm_event(self, rhythm: RhythmEvent):
        """
        Process rhythm events and integrate them into the graph.
        """
        self.add_node(
            rhythm.pattern_id,
            type='rhythm',
            pattern=rhythm.pattern,
            tempo=rhythm.tempo
        )
        logger.info(f'Processed rhythm event: {rhythm.pattern_id} with pattern: {rhythm.pattern} and tempo: {rhythm.tempo}')
        
        # Connect rhythms to chords or notes exhaustively
        # Example: Connect to the most recent chord and note
        last_chord = self._get_last_chord()
        last_note = self._get_last_note()
        if last_chord:
            self.add_edge(
                last_chord.symbol,
                rhythm.pattern_id,
                rhythm=True,
                weight=5
            )
            logger.debug(f'Added edge from {last_chord.symbol} to rhythm {rhythm.pattern_id}')
        if last_note:
            self.add_edge(
                last_note.pitch,
                rhythm.pattern_id,
                rhythm=True,
                weight=5
            )
            logger.debug(f'Added edge from {last_note.pitch} to rhythm {rhythm.pattern_id}')

    def _get_last_chord(self) -> ChordEvent:
        """
        Retrieve the last chord event from the graph.
        """
        chord_nodes = [node for node, attrs in self.graph.nodes(data=True) 
                        if attrs.get('type') == 'chord']
        if chord_nodes:
            last_chord = chord_nodes[-1]
            logger.debug(f'Last chord retrieved: {last_chord}')
            return self._lookup_chord_event(last_chord)
        logger.warning('No last chord found.')
        return None

    def _lookup_chord_event(self, chord_symbol: str) -> ChordEvent:
        """
        Lookup the ChordEvent object based on its symbol.
        """
        for node, attrs in self.graph.nodes(data=True):
            if node == chord_symbol and attrs.get('type') == 'chord':
                logger.debug(f'ChordEvent found for symbol: {chord_symbol}')
                return ChordEvent(symbol=node, type=attrs.get('type'), degrees=attrs.get('degrees'))
        logger.warning(f'ChordEvent not found for symbol: {chord_symbol}')
        return ChordEvent(symbol=chord_symbol, type='chord', degrees=[])

    def _get_last_note(self) -> NoteEvent:
        """
        Retrieve the last note event from the graph.
        """
        note_nodes = [node for node, attrs in self.graph.nodes(data=True) 
                        if attrs.get('type') == 'note']
        if note_nodes:
            last_note = note_nodes[-1]
            logger.debug(f'Last note retrieved: {last_note}')
            return self._lookup_note_event(last_note)
        logger.warning('No last note found.')
        return None

    def _lookup_note_event(self, note_pitch: str) -> NoteEvent:
        """
        Lookup the NoteEvent object based on its pitch.
        """
        for node, attrs in self.graph.nodes(data=True):
            if node == note_pitch and attrs.get('type') == 'note':
                logger.debug(f'NoteEvent found for pitch: {note_pitch}')
                return NoteEvent(pitch=node, duration=attrs.get('duration', 0), intensity=attrs.get('intensity', 0))
        logger.warning(f'NoteEvent not found for pitch: {note_pitch}')
        return NoteEvent(pitch=note_pitch, duration=0, intensity=0)

    def _process_timbre_event(self, timbre: TimbreEvent):
        """
        Process timbre events and integrate them into the graph.
        """
        self.add_node(
            timbre.instrument,
            type='timbre',
            characteristics=timbre.characteristics
        )
        logger.info(f'Processed timbre event: {timbre.instrument} with characteristics: {timbre.characteristics}')
        
        # Connect timbre nodes to other relevant nodes exhaustively, e.g., all notes and chords
        connected_nodes = self._get_connected_nodes()
        for node in connected_nodes:
            self.add_edge(
                timbre.instrument,
                node,
                timbre=True,
                weight=4
            )
            logger.debug(f'Added edge from timbre {timbre.instrument} to {node}')

    def _get_connected_nodes(self) -> List[str]:
        """
        Retrieve nodes that should be connected to timbre events.
        """
        # Connect to all note and chord nodes
        connected_nodes = [node for node, attrs in self.graph.nodes(data=True) 
                if attrs.get('type') in ['note', 'chord']]
        logger.debug(f'Connected nodes for timbre: {connected_nodes}')
        return connected_nodes

    def _process_other_event(self, other: OtherEvent):
        """
        Process other types of events and integrate them into the graph.
        """
        self.add_node(
            other.identifier,
            type='other',
            description=other.description
        )
        logger.info(f'Processed other event: {other.identifier} with description: {other.description}')
        
        # Define connections based on the nature of the other event
        related_nodes = self._find_related_nodes(other)
        for node in related_nodes:
            self.add_edge(
                other.identifier,
                node,
                other=True,
                weight=3
            )
            logger.debug(f'Added edge from other event {other.identifier} to {node}')

    def _find_related_nodes(self, other: OtherEvent) -> List[str]:
        """
        Find nodes related to the other event based on specific criteria.
        """
        # Example implementation: relate to all motifs
        related_nodes = [node for node, attrs in self.graph.nodes(data=True) 
                if attrs.get('type') == 'motif']
        logger.debug(f'Related nodes for other event: {related_nodes}')
        return related_nodes

    def _detect_motifs(self, events: List):
        """
        Detect higher-level motifs or patterns from the events.
        """
        motifs = self._find_motifs(events)
        for motif in motifs:
            self.add_node(
                motif['id'],
                type='motif',
                elements=motif['elements']
            )
            logger.info(f'Detected motif: {motif["id"]} with elements: {motif["elements"]}')
            # Connect motifs to relevant nodes exhaustively
            for element in motif['elements']:
                self.add_edge(
                    motif['id'],
                    element,
                    motif_connection=True,
                    weight=6
                )
                logger.debug(f'Added motif connection from {motif["id"]} to {element}')

    def _find_motifs(self, events: List) -> List[Dict]:
        """
        Analyze events to find recurring motifs.
        """
        motifs = []
        sequence = [event.symbol if isinstance(event, ChordEvent) else event.pitch 
                    for event in events if isinstance(event, (ChordEvent, NoteEvent))]
        min_motif_length = 3
        max_motif_length = 6
        for length in range(min_motif_length, max_motif_length + 1):
            for i in range(len(sequence) - length + 1):
                motif_seq = sequence[i:i+length]
                occurrences = [j for j in range(len(sequence) - length +1) 
                                if sequence[j:j+length] == motif_seq]
                if len(occurrences) > 1:
                    motif_id = f"motif_{length}_{'_'.join(motif_seq)}"
                    motifs.append({
                        'id': motif_id,
                        'elements': motif_seq
                    })
                    logger.debug(f'Found motif: {motif_id} with sequence: {motif_seq}')
        # Remove duplicate motifs
        unique_motifs = {}
        for m in motifs:
            unique_motifs[m['id']] = m
        logger.info(f'Unique motifs detected: {list(unique_motifs.keys())}')
        return list(unique_motifs.values())

    def _determine_weight(self, next_chord: str) -> int:
        """
        Determines the weight of transitioning to the next chord based on its functional role.
        """
        role_weights = {
            'tonic': 15,
            'dominant': 12,
            'secondary_dominant': 12,
            'subdominant': 10,
            'modal_dominant': 11,
            'modal_subdominant': 9,
            'unknown': 8
        }
        role = self.functional_roles.get(next_chord, 'unknown')
        weight = role_weights.get(role, 8)
        logger.debug(f'Determined weight for {next_chord} with role {role}: {weight}')
        return weight

    def decide_improvisation(self, current_context):
        """
        Make an improvisation decision based on the current context and graph state.
        """
        logger.info('Deciding improvisation...')
        # If quick response needed, use minimal context
        if self._needs_quick_response(current_context):
            return self._quick_improv_decision(current_context)
        else:
            # Use full context for a nuanced decision
            return self._detailed_improv_decision(current_context)

    def _needs_quick_response(self, context):
        """
        Determine if a quick response is needed based on the context.
        """
        # Determine if the remaining time is below the threshold
        quick_response_needed = context.get('time_remaining', 0) < self.threshold_time
        logger.debug(f'Quick response needed: {quick_response_needed}')
        return quick_response_needed

    def _quick_improv_decision(self, context):
        """
        Generate a quick improvisation decision using minimal input.
        """
        # Use deterministic music theory engine as fallback
        return self._music_theory_engine(context)

    def _detailed_improv_decision(self, context):
        """
        Generate a detailed improvisation decision using full analysis.
        """
        # Use accumulated graph data to make a decision
        improv_choice = self._analyze_graph_for_improv(context)
        # If analysis fails, fallback to music theory engine
        if not improv_choice:
            logger.warning('Detailed improvisation decision failed, falling back to music theory engine.')
            return self._music_theory_engine(context)
        return improv_choice

    def _music_theory_engine(self, context):
        """
        Fallback deterministic music theory engine.
        """
        # Implement basic music theory rules to generate an output
        current_chord = context.get('current_chord', self.tonic)
        next_chord = self._next_diatonic_chord(current_chord)
        rhythm = self._default_rhythm()
        notes = self._scale_notes(next_chord)
        logger.info(f'Music theory engine output: chord: {next_chord}, rhythm: {rhythm}, notes: {notes}')
        return {
            'chord': next_chord,
            'rhythm': rhythm,
            'notes': notes
        }

    def _next_diatonic_chord(self, current_chord: str) -> str:
        """
        Determine the next diatonic chord based on the current chord.
        """
        # Use Circle of Fifths transitions
        circle = self.circle_of_fifths.get(current_chord, [])
        if circle:
            logger.debug(f'Next diatonic chord from {current_chord}: {circle[0]}')
            return circle[0]  # Choose the first possible transition
        logger.debug(f'No next diatonic chord found, defaulting to tonic: {self.tonic}')
        return self.tonic  # Default to tonic if no transition found

    def _default_rhythm(self) -> List:
        """
        Provide a default rhythm pattern.
        """
        return ['quarter', 'quarter', 'half']

    def _scale_notes(self, chord: str) -> List[str]:
        """
        Provide a list of scale notes based on the chord using Mingus.
        """
        try:
            chord_notes = chords.from_shorthand(chord)
            logger.debug(f'Scale notes for chord {chord}: {chord_notes}')
            return chord_notes
        except Exception as e:
            logger.error(f'Error retrieving scale notes for chord {chord}: {e}')
            return keys.get_scale(self.key, 'major').ascending()

    def _analyze_graph_for_improv(self, context):
        """
        Analyze the graph to make an informed improvisation choice.
        """
        # Example advanced analysis: find the most connected chord
        chords = [node for node, attrs in self.graph.nodes(data=True) 
                    if attrs.get('type') == 'chord']
        if not chords:
            logger.warning('No chords found for improvisation analysis.')
            return {}
        chord_connections = {chord: self.graph.degree(chord) 
                                for chord in chords}
        if not chord_connections:
            logger.warning('No chord connections found for improvisation analysis.')
            return {}
        # Choose the chord with the highest connections
        next_chord = max(chord_connections, key=chord_connections.get)
        rhythm = self._default_rhythm()
        notes = self._scale_notes(next_chord)
        logger.info(f'Analyzed graph for improv: next chord: {next_chord}, rhythm: {rhythm}, notes: {notes}')
        return {
            'chord': next_chord,
            'rhythm': rhythm,
            'notes': notes
        }

    def _get_current_context(self) -> Dict:
        """
        Retrieve the current context for improvisation decisions.
        """
        # Implement actual context retrieval, such as interfacing with MIDI inputs or a GUI
        # For example, retrieve the current time, active chords, and other real-time data
        current_time = self._retrieve_current_time()
        current_chord = self._retrieve_current_chord()
        context = {
            'time_remaining': self.threshold_time - current_time,
            'current_chord': current_chord
        }
        logger.debug(f'Current context retrieved: {context}')
        return context

    def _retrieve_current_time(self) -> float:
        """
        Retrieve the current elapsed time in the musical piece.
        """
        # Placeholder implementation
        # Should interface with a timer or musical timeline
        return 3.0  # Example elapsed time in seconds

    def _retrieve_current_chord(self) -> str:
        """
        Retrieve the current active chord in the context.
        """
        # Placeholder implementation
        # Should interface with the event stream or current state
        if self.graph:
            chord_nodes = [node for node, attrs in self.graph.nodes(data=True) 
                            if attrs.get('type') == 'chord']
            if chord_nodes:
                logger.debug(f'Current active chord: {chord_nodes[-1]}')
                return chord_nodes[-1]
        logger.debug('No current active chord found, defaulting to tonic.')
        return self.tonic
