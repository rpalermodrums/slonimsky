import itertools
import time
from mingus.core import scales, chords, progressions, intervals
from mingus.core.notes import note_to_int, int_to_note
from mingus.containers import NoteContainer, Note
from mingus.midi import fluidsynth
from collections import defaultdict

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

    def generate_custom_scales(self, num_notes, constraints=None):
        """
        Generates custom scales based on the number of notes and optional constraints.

        :param num_notes: Number of notes in the scale
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
            self.custom_scales.append(Scale(scale_name, list(pattern)))

    def catalog_scales(self, root_note='C'):
        """
        Generates all scales, their rotations, and inversions, then catalogs them.

        :param root_note: The root note for all scales
        """
        self.all_scales = []
        # Process predefined scales
        for scale in self.predefined_scales:
            scale.generate_notes(root_note)
            self.all_scales.append(scale)
            # Generate rotations
            rotations = self.generate_all_rotations(scale)
            for rot in rotations:
                rot.generate_notes(root_note)
                self.all_scales.append(rot)
            # Generate inversion
            inverted = self.generate_inversions(scale)
            inverted.generate_notes(root_note)
            self.all_scales.append(inverted)
            # Optionally, generate rotations of inversions
            inv_rotations = self.generate_all_rotations(inverted)
            for inv_rot in inv_rotations:
                inv_rot.generate_notes(root_note)
                self.all_scales.append(inv_rot)
        # Process custom scales if any
        for scale in self.custom_scales:
            scale.generate_notes(root_note)
            self.all_scales.append(scale)
            # Generate rotations
            rotations = self.generate_all_rotations(scale)
            for rot in rotations:
                rot.generate_notes(root_note)
                self.all_scales.append(rot)
            # Generate inversion
            inverted = self.generate_inversions(scale)
            inverted.generate_notes(root_note)
            self.all_scales.append(inverted)
            # Generate rotations of inversions
            inv_rotations = self.generate_all_rotations(inverted)
            for inv_rot in inv_rotations:
                inv_rot.generate_notes(root_note)
                self.all_scales.append(inv_rot)

    def get_all_scales(self):
        return self.all_scales

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

        :param chord_type: Type of the chord (e.g., 'major')
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

class MelodicPatternGenerator:
    def __init__(self):
        """
        Initializes the MelodicPatternGenerator.
        """
        pass

    def generate_melodic_patterns(self, scale, pattern_length=4):
        """
        Generates melodic patterns based on the scale.

        :param scale: Scale instance
        :param pattern_length: Number of notes in each pattern
        :return: List of melodic patterns, each pattern is a list of notes
        """
        patterns = list(itertools.product(scale.get_notes(), repeat=pattern_length))
        # To manage the number of patterns, limit to combinations without immediate repeats
        filtered_patterns = [p for p in patterns if all(p[i] != p[i+1] for i in range(len(p)-1))]
        return filtered_patterns

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

def play_scale(scale, bpm=120):
    """
    Plays the notes of a scale using FluidSynth.
    """
    notes = scale.get_notes()
    duration = 60 / bpm  # Duration of a quarter note in seconds
    for note in notes:
        n = Note(note)
        n.velocity = 100
        fluidsynth.play_Note(n, channel=1)
        time.sleep(duration)
        fluidsynth.stop_Note(n, channel=1)

def play_chord(chord_notes, duration=2, bpm=120):
    """
    Plays a chord (list of notes) using FluidSynth.
    """
    nc = NoteContainer(chord_notes)
    fluidsynth.play_NoteContainer(nc, channel=1)
    time.sleep(duration * (60 / bpm))
    fluidsynth.stop_NoteContainer(nc, channel=1)

def play_progression(progression_chords, bpm=120):
    """
    Plays a chord progression using FluidSynth.
    """
    duration = 2  # Duration in beats for each chord
    for chord_notes in progression_chords:
        play_chord(chord_notes, duration=duration, bpm=bpm)

def main():
    # Initialize FluidSynth with your SoundFont file
    soundfont = './soundfonts/yamaha-c7-grand-piano.sf2'
    fluidsynth.init(soundfont)
    # Set the instrument (optional)
    fluidsynth.set_instrument(1, 1)  # 1 is the MIDI program number for Acoustic Grand Piano

    # Initialize components
    scale_gen = ScaleGenerator()
    chord_builder = ChordBuilder()
    progression_builder = ProgressionBuilder()
    melodic_gen = MelodicPatternGenerator()
    catalog = Catalog()

    # Step 1: Generate and catalog scales
    root_note = 'C'
    scale_gen.generate_custom_scales(num_notes=7)  # Example: 7-note custom scales
    scale_gen.catalog_scales(root_note=root_note)
    all_scales = scale_gen.get_all_scales()
    for scale in all_scales:
        catalog.add_scale(scale)
        # Play the scale
        print(f"Playing scale: {scale.name}")
        play_scale(scale)

    # Step 2: Build and catalog chords from scales
    # Example: For each scale, build triads on each scale degree
    for scale in all_scales:
        for degree in range(len(scale.get_notes())):
            # Determine the root note for the chord based on the scale degree
            chord_root = scale.get_notes()[degree]
            # For simplicity, use major triads
            chord_type = 'major'  # Placeholder, ideally determined by scale
            chord_notes = chord_builder.build_chord(chord_type, chord_root)
            catalog.add_chord(chord_type, chord_notes)
            # Play the chord
            print(f"Playing chord: {chord_notes}")
            play_chord(chord_notes)

    # Step 3: Create and catalog chord progressions
    # Example: I-IV-V progression in C major
    progression_pattern = ['I', 'IV', 'V']
    progression = progression_builder.build_progression(progression_pattern, 'C')
    catalog.add_progression(progression)
    # Play the progression
    print("Playing progression:")
    play_progression(progression)

    # Step 4: Generate and catalog melodic patterns
    # Example: Generate patterns from the first scale
    if all_scales:
        first_scale = all_scales[0]
        melodic_patterns = melodic_gen.generate_melodic_patterns(first_scale, pattern_length=4)
        # To prevent explosion, limit to first 10 patterns
        for pattern in melodic_patterns[:10]:
            print(f"Melodic Pattern: {pattern}")
            # Play the melodic pattern
            for note in pattern:
                n = Note(note)
                n.velocity = 100
                fluidsynth.play_Note(n, channel=1)
                time.sleep(0.5)  # Adjust the duration as needed
                fluidsynth.stop_Note(n, channel=1)

    # Step 5: Display the catalog
    catalog.display_catalog()

if __name__ == "__main__":
    # Create a file to store the output
    with open('./data/output.txt', 'w') as output_file:
        # Redirect print statements to the file
        import sys
        original_stdout = sys.stdout
        sys.stdout = output_file

        # Run the main function
        main()

        # Restore the original stdout
        sys.stdout = original_stdout

    print("Output has been saved to './data/output.txt'")
