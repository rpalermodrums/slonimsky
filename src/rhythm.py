import random
from typing import List


class RhythmicPatternGenerator:
    def __init__(self):
        """
        Initializes the RhythmicPatternGenerator with predefined rhythm types.
        """
        self.rhythm_types = {
            'straight': [1, 1, 1, 1],  # Four quarter notes
            'syncopated': [0.5, 1.5, 0.5, 1.5],  # Eighth and dotted quarter notes
            'triplet': [1/3, 1/3, 1/3] * 4,  # Triplet eighth notes
            'half': [2, 2],  # Two half notes
            'mixed': [1, 0.5, 1.5, 1],  # Mixed durations
            'rests': [1, 'rest', 1, 'rest'],  # Alternating notes and rests
            # Add more rhythm types as needed
        }

    def generate_rhythmic_pattern(self, rhythm_type='straight', pattern_length=4):
        """
        Generates a rhythmic pattern based on the specified type and length.

        :param rhythm_type: Type of rhythm to generate (e.g., 'straight', 'syncopated')
        :param pattern_length: Number of beats or measures to generate
        :return: List representing the rhythmic pattern (durations and rests)
        """
        if rhythm_type not in self.rhythm_types:
            raise ValueError(f"Rhythm type '{rhythm_type}' not recognized. Available types: {list(self.rhythm_types.keys())}")

        base_pattern = self.rhythm_types[rhythm_type]
        pattern = []
        for _ in range(pattern_length):
            pattern.extend(base_pattern)
        return pattern[:pattern_length * len(base_pattern)]

    def generate_random_rhythmic_pattern(self, pattern_length=4):
        """
        Generates a random rhythmic pattern.

        :param pattern_length: Number of beats or measures to generate
        :return: List representing the rhythmic pattern (durations and rests)
        """
        possible_durations = [0.5, 1, 1.5, 2, 'rest']
        pattern = []
        for _ in range(pattern_length):
            duration = random.choice(possible_durations)
            pattern.append(duration)
        return pattern

    def generate_custom_rhythmic_pattern(self, custom_durations: List[float]):
        """
        Generates a rhythmic pattern based on custom durations.

        :param custom_durations: List of durations (in beats) and/or 'rest'
        :return: List representing the rhythmic pattern
        """
        return custom_durations