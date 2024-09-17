import random
from typing import List, Type

from mingus.core.scales import (
    Aeolian,
    Bachian,
    Chromatic,
    Dorian,
    HarmonicMajor,
    HarmonicMinor,
    Ionian,
    Locrian,
    Lydian,
    Major,
    MelodicMinor,
    MinorNeapolitan,
    Mixolydian,
    NaturalMinor,
    Octatonic,
    Phrygian,
    WholeTone,
)
from mingus.core import chords, intervals, notes

class Scale:
    def __init__(self, name: str, mingus_scale_cls=None, root_note: str = 'C', notes: List[str] = None):
        """
        Initializes a Scale with a name, Mingus scale class, and root note.

        :param name: Name of the scale
        :param mingus_scale_cls: Mingus Scale subclass (e.g., scales.Major)
        :param root_note: Root note of the scale
        :param notes: Optional list of notes (overrides mingus_scale)
        """
        self.name = name
        self.root_note = root_note
        self.mingus_scale_cls = mingus_scale_cls

        if notes is not None:
            self.notes = notes
        elif mingus_scale_cls is not None:
            self.mingus_scale = mingus_scale_cls(self.root_note)
            self.notes = self.generate_notes()
        else:
            self.notes = []

    def generate_notes(self) -> List[str]:
        """
        Generates the notes of the scale.

        :return: List of note names.
        """
        return self.mingus_scale.ascending()

    def rotate(self, steps: int = 1) -> 'Scale':
        """
        Rotates the scale by a number of steps.

        :param steps: Number of steps to rotate.
        :return: New Scale instance with rotated notes.
        """
        rotated_notes = self.notes[steps:] + self.notes[:steps]
        rotated_name = f"{self.name}_rotated_{steps}"
        return Scale(rotated_name, self.mingus_scale_cls, self.root_note, notes=rotated_notes)

    def invert(self) -> 'Scale':
        """
        Inverts the scale by reflecting its intervals around the tonic.

        :return: New Scale instance with inverted notes.
        """
        inverted_intervals = self._invert_intervals()
        inverted_notes = [self.root_note]
        current_note = self.root_note

        for interval in inverted_intervals:
            try:
                current_note_int = notes.note_to_int(current_note)
                next_note_int = (current_note_int + interval) % 12
                next_note = notes.int_to_note(next_note_int)
                inverted_notes.append(next_note)
                current_note = next_note
            except Exception as e:
                print(f"Error inverting scale {self.name}: {e}")
                break

        inverted_name = f"{self.name}_inverted"
        return Scale(inverted_name, None, self.root_note, notes=inverted_notes)

    def _invert_intervals(self) -> List[int]:
        """
        Inverts the intervals of the scale around the tonic.

        :return: List of inverted intervals in semitones.
        """
        ascending_notes = self.notes  # Use the current notes
        intervals_list = []
        for i in range(1, len(ascending_notes)):
            interval = intervals.measure(ascending_notes[i - 1], ascending_notes[i]) % 12
            intervals_list.append(interval)

        # Invert intervals: each interval becomes its complement to 12
        inverted_intervals = [(12 - interval) % 12 for interval in intervals_list]
        return inverted_intervals

    def __str__(self) -> str:
        return f"Scale: {self.name}, Notes: {self.notes}"


class ScaleGenerator:
    def __init__(self):
        """
        Initializes the ScaleGenerator with a list of available Mingus scale classes.
        """
        self.available_scale_classes = [
            Aeolian,
            Bachian,
            Chromatic,
            Dorian,
            HarmonicMajor,
            HarmonicMinor,
            Ionian,
            Locrian,
            Lydian,
            Major,
            MelodicMinor,
            MinorNeapolitan,
            Mixolydian,
            NaturalMinor,
            Octatonic,
            Phrygian,
            WholeTone
        ]
        self.scales: List[Scale] = []

    def generate_custom_scales(self, root_note: str) -> None:
        """
        Generates scales based on the specified number of notes and root note.

        :param root_note: Root note for the scales.
        """
        self.scales.clear()
        for scale_cls in self.available_scale_classes:
            try:
                scale_name = f"{root_note}_{scale_cls.__name__}"
                scale = Scale(name=scale_name, mingus_scale_cls=scale_cls, root_note=root_note)
                self.scales.append(scale)
            except Exception as e:
                print(f"Error generating scale {scale_cls.__name__} for root note {root_note}: {e}")

    def catalog_scales(self, root_note: str) -> None:
        """
        Generates additional patterns (rotations and inversions) for each scale.

        :param root_note: Root note used for generating scales.
        """
        for scale in self.scales.copy():
            # Generate all possible rotations for the scale
            for steps in range(1, len(scale.notes)):
                rotated_scale = scale.rotate(steps)
                self.scales.append(rotated_scale)

            # Generate inversion of the scale
            inverted_scale = scale.invert()
            self.scales.append(inverted_scale)

    def get_all_scales(self) -> List[Scale]:
        """
        Retrieves all generated scales.

        :return: List of Scale instances.
        """
        return self.scales


class ChordBuilder:
    def __init__(self):
        """
        Initializes the ChordBuilder with necessary configurations.
        """
        pass  # Implement chord building logic as needed

    def build_chord(self, chord_symbol: str, root_note: str) -> List[str]:
        """
        Builds a chord based on the chord symbol and root note.

        :param chord_symbol: Chord symbol (e.g., 'm7', 'maj7')
        :param root_note: Root note of the chord
        :return: List of note names constituting the chord
        """
        # Example implementation using Mingus
        try:
            chord_notes = chords.from_shorthand(chord_symbol)
            return chord_notes
        except Exception as e:
            print(f"Error building chord {chord_symbol}: {e}")
            return []


class ProgressionBuilder:
    def __init__(self):
        """
        Initializes the ProgressionBuilder with necessary configurations.
        """
        pass  # Implement progression building logic as needed

    def build_progression(self, progression_pattern: List[str], root_note: str) -> List[List[str]]:
        """
        Builds a chord progression based on the provided pattern and root note.

        :param progression_pattern: List of chord symbols (e.g., ['I', 'IV', 'V'])
        :param root_note: Root note for the progression
        :return: List of chords, each represented as a list of note names
        """
        progression = []
        for chord_symbol in progression_pattern:
            actual_chord = self.translate_roman_numeral(chord_symbol, root_note)
            chord_notes = self.build_chord(actual_chord, root_note)
            progression.append(chord_notes)
        return progression

    def build_chord(self, chord_symbol: str, root_note: str) -> List[str]:
        """
        Builds a chord based on the chord symbol and root note.

        :param chord_symbol: Chord symbol (e.g., 'm7', 'maj7', 'C', 'F')
        :param root_note: Root note of the chord
        :return: List of note names constituting the chord
        """
        # Reuse ChordBuilder
        chord_builder = ChordBuilder()
        return chord_builder.build_chord(chord_symbol, root_note)

    def translate_roman_numeral(self, numeral: str, root_note: str) -> str:
        """
        Translates a Roman numeral chord symbol to an actual chord symbol based on the key.

        :param numeral: Roman numeral representing the chord (e.g., 'I', 'iv', 'V')
        :param root_note: Root note of the key
        :return: Translated chord symbol (e.g., 'C', 'Fm', 'G')
        """
        roman_numerals = {
            'I': 'maj',
            'II': 'dim',
            'III': 'm',
            'IV': 'maj',
            'V': 'maj',
            'VI': 'm',
            'VII': 'dim'
        }

        numeral = numeral.upper()
        is_minor = numeral.islower()
        numeral_key = numeral.upper()

        if numeral_key not in roman_numerals:
            print(f"Error: Unsupported Roman numeral '{numeral}'.")
            return numeral  # Return as-is; build_chord will handle invalid symbols

        chord_type = roman_numerals[numeral_key]

        # Determine the scale to use (major key assumed)
        scale = Major(root_note).ascending()

        # Map Roman numeral to scale degree
        degree_map = {
            'I': 0,
            'II': 1,
            'III': 2,
            'IV': 3,
            'V': 4,
            'VI': 5,
            'VII': 6
        }

        root_index = degree_map.get(numeral_key, 0)
        chord_root = scale[root_index]

        # Determine chord quality
        if chord_type == 'maj':
            chord_symbol = chord_root
        elif chord_type == 'm':
            chord_symbol = f"{chord_root}m"
        elif chord_type == 'dim':
            chord_symbol = f"{chord_root}dim"
        else:
            chord_symbol = chord_root  # Default to major if unknown

        return chord_symbol


class MelodicPatternGenerator:
    def __init__(self):
        """
        Initializes the MelodicPatternGenerator with necessary configurations.
        """
        pass  # Implement melodic pattern generation logic as needed

    def generate_pattern(self, scale: Scale) -> List[str]:
        """
        Generates a melodic pattern based on the provided scale.

        :param scale: Scale instance
        :return: List of note names representing the melodic pattern
        """
        # Example implementation: random walk within the scale
        pattern = []
        current_index = random.randint(0, len(scale.notes) - 1)
        for _ in range(8):  # Generate 8 notes
            pattern.append(scale.notes[current_index])
            step = random.choice([-1, 0, 1])  # Move up, stay, or move down
            current_index = max(0, min(current_index + step, len(scale.notes) - 1))
        return pattern