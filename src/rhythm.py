import random
from typing import List, Union, Dict, Callable
import itertools
import math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RhythmicPatternGenerator:
    def __init__(self, tempo: int = 120):
        """
        Initializes the RhythmicPatternGenerator with predefined rhythm types and tempo.
        """
        self.tempo = tempo  # Beats per minute
        self.beat_duration = 60 / self.tempo  # Duration of a beat in seconds
        self.rhythm_types: Dict[str, Dict[str, Union[int, Callable]]] = {
            'straight': {'pulses': 4, 'steps': 4},  # Four beats evenly distributed
            'syncopated': {'pulses': 2, 'steps': 4},  # Two accented beats in four steps
            'triplet': {'pulses': 3, 'steps': 4},  # Triplet pattern over four steps
            'half': {'pulses': 2, 'steps': 2},  # Two half notes
            'mixed': {'pulses': 5, 'steps': 8},  # Mixed durations using 5 pulses in 8 steps
            'rests': {'pulses': 2, 'steps': 4},  # Patterns with rests
        }
        logger.info("RhythmicPatternGenerator initialized with tempo: %d BPM", self.tempo)

    def generate_euclidean_rhythm(self, pulses: int, steps: int) -> List[int]:
        """
        Generates a Euclidean rhythm based on the number of pulses and steps.

        :param pulses: Number of pulses (onsets) in the rhythm
        :param steps: Total number of steps (slots) in the rhythm
        :return: List representing the rhythm with 1s for pulses and 0s for rests
        """
        if pulses > steps:
            logger.error("Number of pulses cannot exceed number of steps.")
            raise ValueError("Number of pulses cannot exceed number of steps.")

        pattern = []
        counts = []
        remainders = []
        divisor = steps - pulses
        remainders.append(pulses)
        logger.debug("Starting Euclidean rhythm generation with pulses: %d, steps: %d", pulses, steps)
        
        while True:
            quotient, remainder = divmod(remainders[-1], divisor)
            counts.append(quotient)
            remainders.append(remainder)
            if remainders[-1] <= 1:
                break
            divisor = counts[-1]
        counts.append(divisor)

        def build(pattern, counts, remainders):
            if not remainders:
                return pattern
            for i in range(counts[0]):
                pattern += build([], counts[1:], remainders[1:])
            if remainders[0]:
                pattern += [0]
            return pattern

        pattern = build([], counts, remainders)
        logger.debug("Generated Euclidean pattern: %s", pattern)
        # Truncate or pad the pattern to match the exact number of steps
        return pattern[:steps].tolist() if hasattr(pattern, 'tolist') else pattern[:steps]

    def generate_rhythmic_pattern(self, rhythm_type='straight', pattern_length=4) -> List[Union[float, str]]:
        """
        Generates a rhythmic pattern based on the specified type and length.

        :param rhythm_type: Type of rhythm to generate (e.g., 'straight', 'syncopated')
        :param pattern_length: Number of measures to generate
        :return: List representing the rhythmic pattern (durations and rests)
        """
        if rhythm_type not in self.rhythm_types:
            logger.error("Rhythm type '%s' not recognized. Available types: %s", rhythm_type, list(self.rhythm_types.keys()))
            raise ValueError(f"Rhythm type '{rhythm_type}' not recognized. Available types: {list(self.rhythm_types.keys())}")

        rhythm_params = self.rhythm_types[rhythm_type]
        pulses = rhythm_params['pulses']
        steps = rhythm_params['steps']
        logger.info("Generating rhythmic pattern of type '%s' with length %d", rhythm_type, pattern_length)

        euclidean_pattern = self.generate_euclidean_rhythm(pulses, steps)
        pattern = []
        for _ in range(pattern_length):
            for step in euclidean_pattern:
                if step == 1:
                    pattern.append(self.beat_duration)  # Duration of the hit
                else:
                    pattern.append('rest')  # Rest

        logger.debug("Generated rhythmic pattern: %s", pattern)
        return pattern

    def generate_schillinger_rhythm(self, numerator: int, denominator: int) -> List[float]:
        """
        Generates rhythmic resultants based on Schillinger's interference theory.

        :param numerator: Number of pulses in the first rhythm
        :param denominator: Number of pulses in the second rhythm
        :return: List representing the rhythmic pattern (durations between accents)
        """
        lcm = self._lcm(numerator, denominator)
        pattern = []
        logger.debug("Generating Schillinger rhythm with numerator: %d, denominator: %d", numerator, denominator)
        
        for i in range(lcm):
            if i % (lcm // numerator) == 0 and i % (lcm // denominator) == 0:
                pattern.append('both')
            elif i % (lcm // numerator) == 0:
                pattern.append('num')
            elif i % (lcm // denominator) == 0:
                pattern.append('den')
            else:
                pattern.append('rest')
        durations = self._convert_events_to_durations(pattern)
        logger.debug("Generated Schillinger rhythm: %s", durations)
        return durations

    def generate_rhythmic_grouping(self, pattern: List[float]) -> List[List[float]]:
        """
        Groups a rhythmic pattern based on Cooper and Meyer's grouping principles.

        :param pattern: List of durations
        :return: List of grouped durations
        """
        groups = []
        i = 0
        logger.debug("Generating rhythmic grouping for pattern: %s", pattern)
        
        while i < len(pattern):
            group = [pattern[i]]
            # Group notes into twos or threes if they are short
            if isinstance(pattern[i], float) and pattern[i] <= self.beat_duration:
                j = i + 1
                while j < len(pattern) and isinstance(pattern[j], float) and sum(group) + pattern[j] <= 2 * self.beat_duration:
                    group.append(pattern[j])
                    j += 1
                i = j
            else:
                i += 1
            groups.append(group)
        logger.debug("Grouped rhythmic pattern: %s", groups)
        return groups

    def augment_rhythm(self, pattern: List[float], factor: float) -> List[float]:
        """
        Augments or diminishes a rhythmic pattern by a factor.

        :param pattern: Original rhythmic pattern
        :param factor: Factor by which to augment (>1) or diminish (<1) the durations
        :return: Transformed rhythmic pattern
        """
        augmented_pattern = [duration * factor if isinstance(duration, float) else duration for duration in pattern]
        logger.debug("Augmented rhythm with factor %f: %s", factor, augmented_pattern)
        return augmented_pattern

    def permute_rhythm(self, pattern: List[float]) -> List[List[float]]:
        """
        Generates all permutations of a rhythmic pattern.

        :param pattern: Original rhythmic pattern
        :return: List of all permutations of the pattern
        """
        permutations = list(itertools.permutations(pattern))
        logger.debug("Generated permutations of rhythm: %s", permutations)
        return permutations

    def rotate_rhythm(self, pattern: List[float]) -> List[List[float]]:
        """
        Generates all rotations (cyclic permutations) of a rhythmic pattern.

        :param pattern: Original rhythmic pattern
        :return: List of rotations of the pattern
        """
        rotations = []
        n = len(pattern)
        logger.debug("Generating rotations for rhythm: %s", pattern)
        
        for i in range(n):
            rotation = pattern[i:] + pattern[:i]
            rotations.append(rotation)
        logger.debug("Generated rotations: %s", rotations)
        return rotations

    def generate_polyrhythm(self, pulses: List[int]) -> List[float]:
        """
        Generates a polyrhythmic pattern based on given pulses.

        :param pulses: List of pulses for each rhythm (e.g., [3, 4] for a 3:4 polyrhythm)
        :return: Rhythmic pattern representing the polyrhythm
        """
        lcm = self._lcm_multiple(pulses)
        pattern = ['rest'] * lcm
        logger.debug("Generating polyrhythm with pulses: %s", pulses)
        
        for pulse in pulses:
            step = lcm // pulse
            for i in range(0, lcm, step):
                pattern[i] = 'hit' if pattern[i] == 'rest' else 'hit+'
        durations = self._convert_events_to_durations(pattern)
        logger.debug("Generated polyrhythmic pattern: %s", durations)
        return durations

    def _convert_events_to_durations(self, events: List[str]) -> List[float]:
        """
        Converts a sequence of events to durations.

        :param events: List of events ('hit', 'rest', 'hit+', 'both', etc.)
        :return: List of durations between events
        """
        durations = []
        count = 0
        logger.debug("Converting events to durations: %s", events)
        
        for event in events:
            if event != 'rest':
                if count > 0:
                    durations.append(count * self.beat_duration)
                durations.append(self.beat_duration)  # Duration of the hit
                count = 0
            else:
                count += 1
        if count > 0:
            durations.append(count * self.beat_duration)
        logger.debug("Converted durations: %s", durations)
        return durations

    def _lcm(self, a: int, b: int) -> int:
        """
        Computes the least common multiple of two integers.

        :param a: First integer
        :param b: Second integer
        :return: Least common multiple
        """
        lcm = abs(a * b) // math.gcd(a, b)
        logger.debug("Computed LCM of %d and %d: %d", a, b, lcm)
        return lcm

    def _lcm_multiple(self, numbers: List[int]) -> int:
        """
        Computes the least common multiple of a list of integers.

        :param numbers: List of integers
        :return: Least common multiple
        """
        lcm = numbers[0]
        logger.debug("Computing LCM for numbers: %s", numbers)
        
        for number in numbers[1:]:
            lcm = self._lcm(lcm, number)
        logger.debug("Computed LCM for list: %d", lcm)
        return lcm