import asyncio
import argparse
import concurrent.futures
import sys
import os
import time
import json
from collections import defaultdict
from functools import lru_cache

from mingus.core import scales, chords, progressions, intervals, notes
from mingus.core.notes import note_to_int, int_to_note
from mingus.containers import NoteContainer, Note
from mingus.midi import fluidsynth

# Constants
OCTAVE = 12  # Number of semitones in an octave

class Scale:
    def __init__(self, name, intervals_pattern):
        """
        Initializes a Scale with a name and a pattern of intervals.

        :param name: Name of the scale
        :param intervals_pattern: List of intervals in semitones
        """
        self.name = name
        self.intervals_pattern = intervals_pattern
        self.notes = []

    def generate_notes(self, root_note):
        """
        Generates the notes of the scale starting from the root_note.

        :param root_note: The starting note of the scale (e.g., 'C')
        """
        root_int = note_to_int(root_note)
        current_int = root_int
        self.notes = [int_to_note(current_int)]
        for interval in self.intervals_pattern:
            current_int = (current_int + interval) % OCTAVE
            self.notes.append(int_to_note(current_int))
        # Remove the octave duplication
        self.notes = self.notes[:-1]

    def get_notes(self):
        return self.notes

    def rotate(self, steps=1):
        """
        Rotates the scale by a number of steps.

        :param steps: Number of rotations
        :return: New Scale instance with rotated intervals
        """
        rotated_intervals = self.intervals_pattern[steps:] + self.intervals_pattern[:steps]
        rotated_name = f"{self.name}_rotated_{steps}"
        return Scale(rotated_name, rotated_intervals)

    def invert(self):
        """
        Inverts the scale intervals.

        :return: New Scale instance with inverted intervals
        """
        inverted_intervals = [OCTAVE - interval for interval in self.intervals_pattern[::-1]]
        inverted_name = f"{self.name}_inverted"
        return Scale(inverted_name, inverted_intervals)

    def __str__(self):
        return f"Scale: {self.name}, Intervals: {self.intervals_pattern}, Notes: {self.notes}"
    

class SlonimskyScale(Scale):
    def __init__(self, name, intervals_pattern):
        """
        Initializes a Slonimsky Scale with a name and a pattern of intervals.
        """
        self.name = name
        self.intervals_pattern = intervals_pattern
        self.notes = []

    def generate_notes(self, root_note):
        """
        Generates the notes of the Slonimsky scale starting from the root_note.
        """
        root_int = note_to_int(root_note)
        current_int = root_int
        self.notes = [int_to_note(current_int)]
        for interval in self.intervals_pattern:
            current_int += interval
            self.notes.append(int_to_note(current_int % (OCTAVE * 2)))
        # Remove the octave duplication
        self.notes = self.notes[:-1]

class ScaleGraph:
    def __init__(self, scale):
        """
        Initializes a graph representation of a scale.

        :param scale: Scale instance
        """
        self.graph = defaultdict(list)
        self.scale = scale

    def build_graph(self):
        """
        Builds a graph where each note is a node connected to possible next notes based on the scale.
        """
        notes = self.scale.get_notes()
        num_notes = len(notes)
        for i in range(num_notes):
            current_note = notes[i]
            next_note = notes[(i + 1) % num_notes]
            self.graph[current_note].append(next_note)

    def get_graph(self):
        """
        Returns the graph representation.

        :return: Dictionary representing the adjacency list of the graph
        """
        return self.graph

class ScaleGenerator:
    def __init__(self):
        """
        Initializes the ScaleGenerator with a list of predefined scales.
        """
        self.predefined_scales = self.load_predefined_scales()
        self.custom_scales = []
        self.all_scales = []

    def load_predefined_scales(self):
        """
        Loads a set of predefined scales from Mingus.

        :return: List of Scale instances
        """
        predefined = []
        mingus_scales = {
            'major': scales.Major,
            'natural_minor': scales.NaturalMinor,
            'dorian': scales.Dorian,
            'phrygian': scales.Phrygian,
            'lydian': scales.Lydian,
            'mixolydian': scales.Mixolydian,
            'locrian': scales.Locrian,
            'harmonic_minor': scales.HarmonicMinor,
            'melodic_minor': scales.MelodicMinor,
            'chromatic': scales.Chromatic
            # Add more Mingus scales as needed
        }
        for name, scale_cls in mingus_scales.items():
            scale = scale_cls('C')  # Mingus scales are initialized with a key, not a note
            pattern = [intervals.measure(scale.ascending()[i], scale.ascending()[i+1]) for i in range(len(scale.ascending())-1)]
            predefined.append(Scale(name, pattern))
        return predefined

    def generate_all_rotations(self, scale, max_rotations=None):
        """
        Generates all possible rotations of a scale.

        :param scale: Scale instance
        :param max_rotations: Maximum number of rotations to generate
        :return: List of rotated Scale instances
        """
        rotations = []
        steps = len(scale.intervals_pattern)
        max_rot = steps if not max_rotations else min(max_rotations, steps)
        for i in range(1, max_rot):
            rotated = scale.rotate(steps=i)
            rotations.append(rotated)
        return rotations

    def generate_inversions(self, scale):
        """
        Generates the inversion of a scale.

        :param scale: Scale instance
        :return: Inverted Scale instance
        """
        return scale.invert()

    def generate_custom_scales(self, num_notes, root_note='C', constraints=None):
        """
        Generates custom scales based on the number of notes and optional constraints.

        :param num_notes: Number of notes in the scale
        :param root_note: The starting note of the scale (default 'C')
        :param constraints: Function to filter scale interval patterns
        """
        # Generate all possible interval combinations that sum to OCTAVE
        # Each interval must be at least 1 semitone
        # This is a partition problem
        def partitions(n, k, min_part=1):
            if k == 1:
                yield (n,)
                return
            for i in range(min_part, n - min_part * (k - 1) + 1):
                for p in partitions(n - i, k - 1, min_part):
                    yield (i,) + p

        for pattern in partitions(OCTAVE, num_notes):
            if constraints and not constraints(pattern):
                continue
            scale_name = f"custom_{num_notes}_notes_{'_'.join(map(str, pattern))}"
            custom_scale = Scale(scale_name, list(pattern))
            custom_scale.generate_notes(root_note)
            self.custom_scales.append(custom_scale)

    def generate_barry_harris_scale(self, chord_type, root_note):
        """
        Generates Barry Harris's 6th diminished scale based on the chord type and root note.

        :param chord_type: 'major' or 'minor'
        :param root_note: The root note of the chord (e.g., 'C')
        :return: Barry Harris Scale instance
        """
        if chord_type == 'major':
            # Major 6th chord intervals
            chord_intervals = [0, 4, 7, 9]  # C, E, G, A
        elif chord_type == 'minor':
            # Minor 6th chord intervals
            chord_intervals = [0, 3, 7, 9]  # C, Eb, G, A
        else:
            raise ValueError("Chord type must be 'major' or 'minor'.")

        # Leading-tone diminished chord intervals (starting on the maj7th)
        diminished_intervals = [(i + 1) % OCTAVE for i in [0, 3, 6, 9]]  # For C major: B, D, F, Ab

        # Combine the chord and diminished intervals into an 8-note scale
        bh_intervals = sorted(set(chord_intervals + diminished_intervals))
        bh_intervals_pattern = [(bh_intervals[i+1] - bh_intervals[i]) % OCTAVE for i in range(len(bh_intervals)-1)]
        bh_intervals_pattern.append((OCTAVE - sum(bh_intervals_pattern)) % OCTAVE)  # Complete the octave

        scale_name = f"Barry_Harris_{chord_type}_6th_diminished_{root_note}"
        bh_scale = Scale(scale_name, bh_intervals_pattern)
        bh_scale.generate_notes(root_note)
        return bh_scale

    @lru_cache(maxsize=None)
    def generate_scale(self, intervals_pattern, root_note):
        """
        Generates and caches a scale based on the interval pattern and root note.

        :param intervals_pattern: Tuple of intervals in semitones
        :param root_note: The starting note of the scale (e.g., 'C')
        :return: List of notes in the scale
        """
        root_int = note_to_int(root_note)
        current_int = root_int
        notes = [int_to_note(current_int)]
        for interval in intervals_pattern:
            current_int = (current_int + interval) % OCTAVE
            notes.append(int_to_note(current_int))
        # Remove the octave duplication
        return notes[:-1]

    def catalog_scales(self, root_note='C'):
        """
        Generates all unique scales, their rotations, and inversions, then catalogs them.

        :param root_note: The root note for all scales
        """
        self.all_scales = []
        unique_scales = set()

        # Process predefined scales
        for scale in self.predefined_scales:
            pattern_tuple = tuple(scale.intervals_pattern)
            if pattern_tuple in unique_scales:
                continue
            unique_scales.add(pattern_tuple)
            scale.generate_notes(root_note)
            self.all_scales.append(scale)

            # Generate rotations
            rotations = self.generate_all_rotations(scale)
            for rot in rotations:
                pattern_tuple = tuple(rot.intervals_pattern)
                if pattern_tuple in unique_scales:
                    continue
                unique_scales.add(pattern_tuple)
                rot.generate_notes(root_note)
                self.all_scales.append(rot)

            # Generate inversion
            inverted = self.generate_inversions(scale)
            pattern_tuple = tuple(inverted.intervals_pattern)
            if pattern_tuple not in unique_scales:
                unique_scales.add(pattern_tuple)
                inverted.generate_notes(root_note)
                self.all_scales.append(inverted)

    def generate_all_scales_parallel(self, root_note='C'):
        """
        Generates all unique scales in parallel.

        :param root_note: The root note for all scales
        """
        self.all_scales = []
        unique_scales = set()
        scales_to_process = self.predefined_scales + self.custom_scales

        def process_scale(scale):
            pattern_tuple = tuple(scale.intervals_pattern)
            if pattern_tuple in unique_scales:
                return None
            unique_scales.add(pattern_tuple)
            scale.generate_notes(root_note)
            result_scales = [scale]

            # Generate rotations and inversions
            rotations = self.generate_all_rotations(scale)
            inversions = [self.generate_inversions(scale)]
            all_variants = rotations + inversions

            for variant in all_variants:
                pattern_tuple = tuple(variant.intervals_pattern)
                if pattern_tuple not in unique_scales:
                    unique_scales.add(pattern_tuple)
                    variant.generate_notes(root_note)
                    result_scales.append(variant)
            return result_scales

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_scale, scale) for scale in scales_to_process]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    self.all_scales.extend(result)

    def get_all_scales(self):
        return self.all_scales

    def generate_whole_tone_scale(self, start_note):
        """
        Generates a whole tone scale starting from the given note.

        :param start_note: The starting note (e.g., 'C')
        :return: Scale instance of the whole tone scale
        """
        intervals_pattern = [2] * 6  # Six whole steps cover the octave
        scale_name = f"Whole_Tone_Scale_{start_note}"
        whole_tone_scale = Scale(scale_name, intervals_pattern)
        whole_tone_scale.generate_notes(start_note)
        return whole_tone_scale

    def generate_augmented_scale(self, start_note):
        """
        Generates an augmented scale starting from the given note.

        :param start_note: The starting note (e.g., 'C')
        :return: Scale instance of the augmented scale
        """
        intervals = [3, 1, 3, 1, 3, 1]  # Alternating minor thirds and half steps
        scale_name = f"Augmented_Scale_{start_note}"
        augmented_scale = Scale(scale_name, intervals)
        augmented_scale.generate_notes(start_note)
        return augmented_scale

class ChordBuilder:
    def __init__(self):
        """
        Initializes the ChordBuilder.
        """
        self.chord_types = {
            'major': chords.major_triad,
            'minor': chords.minor_triad,
            'diminished': chords.diminished_triad,
            'augmented': chords.augmented_triad,
            'dominant_seventh': chords.dominant_seventh,
            'major_seventh': chords.major_seventh,
            'minor_seventh': chords.minor_seventh,
            # Add more chord types as needed
        }

    def build_chord(self, chord_type, root_note):
        """
        Builds a chord based on the chord type and root note.

        :param chord_type: Type of the chord (e.g., 'major', 'minor', 'diminished')
        :param root_note: Root note of the chord (e.g., 'C')
        :return: List of notes in the chord
        """
        if chord_type not in self.chord_types:
            raise ValueError(f"Chord type '{chord_type}' not recognized.")
        chord = self.chord_types[chord_type](root_note)
        return chord

class ProgressionBuilder:
    def __init__(self):
        """
        Initializes the ProgressionBuilder.
        """
        pass

    def build_progression(self, progression_pattern, key):
        """
        Builds a chord progression based on the pattern and key.

        :param progression_pattern: List of scale degrees (e.g., ['I', 'IV', 'V'])
        :param key: Key for the progression (e.g., 'C')
        :return: List of chords, each chord is a list of notes
        """
        # Use Mingus progressions to get chord names
        chord_names = progressions.to_chords(progression_pattern, key)
        return chord_names

    def build_principal_interval_progression(self, start_note, interval):
        """
        Builds a progression where chords are a fixed interval apart.

        :param start_note: The starting note (e.g., 'C')
        :param interval: Interval between chords in semitones
        :return: List of chord root notes
        """
        start_int = note_to_int(start_note)
        progression = []
        current_int = start_int
        while True:
            note = int_to_note(current_int % OCTAVE)
            progression.append(note)
            current_int = (current_int + interval) % OCTAVE
            if current_int == start_int:
                break
        return progression

class MelodicPatternGenerator:
    def __init__(self):
        """
        Initializes the MelodicPatternGenerator.
        """
        self.pattern_cache = {}

    def generate_melodic_patterns(self, scale, pattern_length=4):
        """
        Generates melodic patterns based on the scale using DP.

        :param scale: Scale instance
        :param pattern_length: Number of notes in each pattern
        :return: Generator of melodic patterns
        """
        notes = scale.get_notes()
        cache_key = (tuple(notes), pattern_length)
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]

        def helper(current_pattern):
            if len(current_pattern) == pattern_length:
                yield current_pattern
                return
            for note in notes:
                if not current_pattern or note != current_pattern[-1]:
                    yield from helper(current_pattern + [note])

        self.pattern_cache[cache_key] = helper([])
        return self.pattern_cache[cache_key]

    def generate_cyclic_interval_pattern(self, start_note, interval, iterations):
        """
        Generates a cyclic interval pattern starting from a note.

        :param start_note: The starting note (e.g., 'C')
        :param interval: Interval in semitones
        :param iterations: Number of iterations
        :return: List of notes in the pattern
        """
        start_int = note_to_int(start_note)
        pattern = []
        for i in range(iterations):
            pitch = (start_int + i * interval) % OCTAVE  # Use modulo OCTAVE to keep within 0-11 range
            pattern.append(int_to_note(pitch))
        return pattern

    def transpose_pattern(self, pattern, shift):
        """
        Transposes a given pattern by a specified number of semitones.

        :param pattern: List of note names (e.g., ['C', 'E', 'G'])
        :param shift: Number of semitones to shift
        :return: Transposed pattern as a list of notes
        """
        transposed = []
        for note in pattern:
            transposed_pitch = (note_to_int(note) + shift) % (OCTAVE * 2)
            transposed.append(int_to_note(transposed_pitch))
        return transposed

    def get_partial_cycle(self, cycle, length):
        """
        Retrieves a partial cycle from a full cycle pattern.

        :param cycle: List of note names representing the full cycle
        :param length: Desired length of the partial cycle
        :return: List of note names representing the partial cycle
        """
        if length > len(cycle):
            return cycle
        return cycle[:length]

    def extend_pattern_across_octaves(self, pattern, octaves):
        """
        Extends a pattern across multiple octaves.

        :param pattern: List of note names
        :param octaves: Number of octaves to span
        :return: Extended pattern as a list of notes
        """
        extended = []
        for octave in range(octaves):
            for note in pattern:
                pitch_int = note_to_int(note) + (OCTAVE * octave)
                extended.append(int_to_note(pitch_int))
        return extended

    def combine_cycles(self, cycles):
        """
        Combines multiple cycles into one sequence.

        :param cycles: List of cycles, each a list of note names
        :return: Combined cycle as a list of notes
        """
        combined = []
        for cycle in cycles:
            combined.extend(cycle)
        return combined

    def generate_major_thirds_cycle_vocabulary(self, start_note):
        """
        Generates a melodic vocabulary based on a cycle of major thirds.

        :param start_note: The starting note (e.g., 'C')
        :return: List of tuples containing note and associated chord type
        """
        vocabulary = []
        # V7 chords cycling by major thirds
        for i in range(3):
            pitch = (note_to_int(start_note) + i * 4) % OCTAVE
            note = int_to_note(pitch)
            vocabulary.append((note, 'V7'))
        # I chords cycling by major thirds
        for i in range(3):
            pitch = (note_to_int(start_note) + i * 4) % OCTAVE
            note = int_to_note(pitch)
            vocabulary.append((note, 'I'))
        return vocabulary

class Catalog:
    def __init__(self):
        """
        Initializes the Catalog to store scales, chords, and progressions.
        """
        self.scales = []
        self.chords = defaultdict(list)  # key: chord type, value: list of chords
        self.progressions = []

    def add_scale(self, scale):
        self.scales.append(scale)
        if isinstance(scale, SlonimskyScale):
            print(f"Added Slonimsky scale: {scale.name}")
        else:
            print(f"Added scale: {scale.name}")

    def add_chord(self, chord_type, chord_notes):
        self.chords[chord_type].append(chord_notes)

    def add_progression(self, progression):
        self.progressions.append(progression)

    def display_catalog(self):
        print("=== Scales ===")
        for scale in self.scales:
            print(scale)
        print("\n=== Chords ===")
        for ctype, chords_list in self.chords.items():
            print(f"{ctype.capitalize()} Chords:")
            for chord in chords_list:
                print(chord)
        print("\n=== Progressions ===")
        for prog in self.progressions:
            print(prog)

def initialize_fluidsynth():
    try:
        print("Initializing FluidSynth...")
        fluidsynth.init('./soundfonts/yamaha-c7-grand-piano.sf2', 'coreaudio')
        fluidsynth.set_instrument(1, 1)  # 1 is the MIDI program number for Acoustic Grand Piano
        print("FluidSynth initialized successfully.")
    except Exception as e:
        print(f"Error initializing FluidSynth: {e}")
        sys.exit(1)

def test_sound():
    try:
        print("Testing sound output...")
        note = Note("C-5")
        fluidsynth.play_Note(note)
        time.sleep(1)
        fluidsynth.stop_Note(note)
        print("Test sound played. Did you hear it?")
    except Exception as e:
        print(f"Error playing test sound: {e}")

def play_scale(scale, bpm=120):
    try:
        print(f"Attempting to play scale: {scale.name}")
        notes = scale.get_notes()
        duration = 60 / bpm  # Duration of a quarter note in seconds
        for note in notes:
            print(f"Playing note: {note}")
            n = Note(note)
            n.velocity = 100
            fluidsynth.play_Note(n)
            time.sleep(duration)
            fluidsynth.stop_Note(n)
        print("Scale playback completed.")
    except Exception as e:
        print(f"Error playing scale: {e}")

async def play_melodic_pattern(pattern, bpm=120):
    """
    Plays a melodic pattern asynchronously using FluidSynth.
    """
    duration = 60 / bpm
    for note in pattern:
        n = Note(note)
        n.velocity = 100
        fluidsynth.play_NoteAsync(n, channel=1)
        await asyncio.sleep(duration)
        fluidsynth.stop_NoteAsync(n, channel=1)

def determine_chord_type(scale, degree):
    """
    Determines the chord type for a given scale degree.

    :param scale: Scale instance
    :param degree: Scale degree (0-based index)
    :return: Chord type as a string
    """
    # Simplified example based on major scale chord qualities
    # In major scale: I, ii, iii, IV, V, vi, vii°
    chord_qualities = ['major', 'minor', 'minor', 'major', 'major', 'minor', 'diminished']
    num_degrees = len(scale.get_notes())
    return chord_qualities[degree % num_degrees]

def validate_root_note(root_note):
    try:
        # Convert the input note to an integer (0-11)
        note_int = notes.note_to_int(root_note)

        # Convert back to a note name (this will use the preferred sharp notation)
        valid_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return valid_notes[note_int]
    except notes.NoteFormatError:
        raise ValueError(f"Invalid root note '{root_note}'. Please enter a valid note (e.g., C, C#, Db, D, etc.)")

def validate_bpm(bpm):
    if bpm <= 30 or bpm > 300:
        raise ValueError(f"BPM '{bpm}' is out of valid range (30-300).")

def validate_interval(interval):
    if interval <= 0 or interval >= 24:
        raise ValueError(f"Interval '{interval}' is out of valid range (1-23).")

def validate_iterations(iterations):
    if iterations <= 0 or iterations > 100:
        raise ValueError(f"Iterations '{iterations}' is out of valid range (1-100).")

def play_progression(progression, bpm=120):
    try:
        print("Attempting to play chord progression.")
        duration = 60 / bpm  # Duration of a quarter note in seconds
        for chord in progression:
            print(f"Playing chord: {chord}")
            for note in chord:
                n = Note(note)
                n.velocity = 100
                fluidsynth.play_Note(n)
            time.sleep(duration)
            for note in chord:
                fluidsynth.stop_Note(Note(note))
        print("Progression playback completed.")
    except Exception as e:
        print(f"Error playing progression: {e}")

def get_user_input():
    parser = argparse.ArgumentParser(description='Musical Pattern Generator')
    parser.add_argument('--root_note', type=str, help='Root note for scales and chords')
    parser.add_argument('--bpm', type=int, help='Tempo in beats per minute')
    parser.add_argument('--progression_pattern', nargs='+', help='Chord progression pattern')
    parser.add_argument('--pattern_start_note', type=str, help='Start note for patterns')
    parser.add_argument('--interval', type=int, help='Interval in semitones for patterns')
    parser.add_argument('--iterations', type=int, help='Number of iterations for patterns')
    parser.add_argument('--num_custom_scales', type=int, help='Number of custom scales to generate')
    parser.add_argument('--num_notes_in_custom_scales', type=int, help='Number of notes in custom scales')

    args = parser.parse_args()

    # Prompt for missing required arguments with defaults
    if not args.root_note:
        args.root_note = input('Enter root note (e.g., C, D#, F) [default: C]: ').strip() or 'C'
    if not args.bpm:
        args.bpm = int(input('Enter BPM (e.g., 120) [default: 240]: ').strip() or 240)
    if not args.progression_pattern:
        progression_input = input('Enter progression pattern (e.g., I IV V) [default: I IV V]: ').strip() or 'I IV V'
        args.progression_pattern = progression_input.split()
    if not args.pattern_start_note:
        args.pattern_start_note = input('Enter start note for patterns [default: C]: ').strip() or 'C'
    if not args.interval:
        args.interval = int(input('Enter interval in semitones [default: 2]: ').strip() or 2)
    if not args.iterations:
        args.iterations = int(input('Enter number of iterations for patterns [default: 8]: ').strip() or 8)
    if not args.num_custom_scales:
        args.num_custom_scales = int(input('Enter number of custom scales to generate [default: 5]: ').strip() or 5)
    if not args.num_notes_in_custom_scales:
        args.num_notes_in_custom_scales = int(input('Enter number of notes in custom scales [default: 7]: ').strip() or 7)

    return args

def main():
    # Get user input first
    args = get_user_input()

    # Validate inputs
    try:
        validate_root_note(args.root_note)
        validate_bpm(args.bpm)
        validate_interval(args.interval)
        validate_iterations(args.iterations)
    except ValueError as e:
        print(f"Input validation error: {e}")
        sys.exit(1)

    # Initialize FluidSynth after user input
    initialize_fluidsynth()

    # Test sound
    test_sound()

    # Proceed to execute main logic with validated and complete arguments
    execute_main(args)

def execute_main(args):
    # Initialize components
    scale_gen = ScaleGenerator()
    chord_builder = ChordBuilder()
    progression_builder = ProgressionBuilder()
    melodic_gen = MelodicPatternGenerator()
    catalog = Catalog()

    # Create the directory for graphs if it doesn't exist
    os.makedirs('./data/graphs', exist_ok=True)

    # Generate and catalog scales
    scale_gen.generate_custom_scales(num_notes=args.num_notes_in_custom_scales, root_note=args.root_note)
    scale_gen.catalog_scales(root_note=args.root_note)
    all_scales = scale_gen.get_all_scales()
    for scale in all_scales:
        catalog.add_scale(scale)
        # Build graph for the scale
        scale_graph = ScaleGraph(scale)
        scale_graph.build_graph()
        graph_output = scale_graph.get_graph()
        print(f"Graph for scale {scale.name}:")
        print(graph_output)
        # Save the graph
        with open(f'./data/graphs/{scale.name}_graph.json', 'w') as graph_file:
            json.dump(graph_output, graph_file)

        # Play the scale
        print(f"Playing scale: {scale.name}")
        play_scale(scale, bpm=args.bpm)

    # Generate and play chord progression
    progression = progression_builder.build_progression(args.progression_pattern, args.root_note)
    catalog.add_progression(progression)
    print("Playing progression:")
    play_progression(progression, bpm=args.bpm)

    # Generate and play cyclic interval pattern
    print("\n=== Cyclic Interval Patterns ===")
    cyclic_pattern = melodic_gen.generate_cyclic_interval_pattern(args.pattern_start_note, args.interval, args.iterations)
    print(f"Cyclic Interval Pattern starting at {args.pattern_start_note} with interval {args.interval}:")
    print(cyclic_pattern)

    # Build graph for the pattern
    pattern_graph = defaultdict(list)
    for i in range(len(cyclic_pattern) - 1):
        current_note = cyclic_pattern[i]
        next_note = cyclic_pattern[i + 1]
        pattern_graph[current_note].append(next_note)
    print(f"Graph for cyclic pattern:")
    print(pattern_graph)
    # Optionally save the pattern graph
    with open('./data/graphs/cyclic_pattern_graph.json', 'w') as graph_file:
        json.dump(pattern_graph, graph_file)

    # Play the cyclic interval pattern
    print("Playing cyclic interval pattern:")
    for note in cyclic_pattern:
        n = Note(note)
        n.velocity = 100
        fluidsynth.play_Note(n, channel=1)
        time.sleep(60 / args.bpm)
        fluidsynth.stop_Note(n, channel=1)

    # Additional code for other patterns and features...

    # Display the catalog
    catalog.display_catalog()

if __name__ == "__main__":
    main()


