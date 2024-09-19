from .base_graph import BaseGraph
from typing import List, Dict
from models import RhythmicPattern
import itertools
import logging

logger = logging.getLogger(__name__)

class RhythmGraphBuilder(BaseGraph):
    def __init__(self, tempo: int = 120):
        super().__init__()
        self.tempo = tempo  # Default tempo
        self.rhythm_systems = self._generate_rhythm_systems()
        self.groupings = self._generate_groupings()
        self.meter = self._set_default_meter()
        logger.info(f"Initialized RhythmGraphBuilder with tempo: {self.tempo}, meter: {self.meter}")

    def build_rhythm_graph(self, rhythms: List[RhythmicPattern]):
        logger.info(f"Building rhythm graph with {len(rhythms)} rhythms.")
        for rhythm in rhythms:
            # Assume rhythm.pattern is a list of durations
            pattern_str = self._pattern_to_str(rhythm.pattern)
            logger.debug(f"Adding node: {pattern_str} with tempo: {rhythm.tempo or self.tempo}, accent: {rhythm.accent}")
            self.add_node(
                pattern_str,
                tempo=rhythm.tempo or self.tempo,
                accent=rhythm.accent,
                grouping=self._determine_grouping(rhythm.pattern),
                meter=self.meter
            )
        
        # Define rhythmic transitions based on rhythmic transformations
        logger.info("Defining rhythmic transitions.")
        for current_rhythm in rhythms:
            for next_rhythm in rhythms:
                if current_rhythm == next_rhythm:
                    continue
                transformations = self._generate_rhythmic_transformations(current_rhythm.pattern)
                if self._pattern_to_str(next_rhythm.pattern) in transformations:
                    weight = self._determine_rhythm_weight(current_rhythm, next_rhythm)
                    logger.debug(f"Adding edge from {self._pattern_to_str(current_rhythm.pattern)} to {self._pattern_to_str(next_rhythm.pattern)} with transformation: True, weight: {weight}")
                    self.add_edge(
                        self._pattern_to_str(current_rhythm.pattern),
                        self._pattern_to_str(next_rhythm.pattern),
                        transformation=True,
                        weight=weight
                    )
                else:
                    # Less preferred transitions
                    logger.debug(f"Adding edge from {self._pattern_to_str(current_rhythm.pattern)} to {self._pattern_to_str(next_rhythm.pattern)} with transformation: False, weight: 5")
                    self.add_edge(
                        self._pattern_to_str(current_rhythm.pattern),
                        self._pattern_to_str(next_rhythm.pattern),
                        transformation=False,
                        weight=5
                    )

    def _generate_rhythm_systems(self) -> Dict:
        """
        Generate rhythmic systems based on Schillinger's Theory of Rhythm.
        Incorporates interference of periodicities to create complex rhythmic patterns.
        """
        rhythm_systems = {}
        periodicities = [1, 2, 3, 4]  # Example periodicities representing different rhythmic cycles

        # Generate resultants by combining periodicities
        for p1, p2 in itertools.combinations(periodicities, 2):
            resultant = self._interfere_periodicities(p1, p2)
            pattern_str = self._pattern_to_str(resultant)
            rhythm_systems[pattern_str] = {
                'periodicities': (p1, p2),
                'resultant': resultant
            }
            logger.debug(f"Generated rhythm system: {pattern_str} with periodicities: {p1}, {p2}")
        
        return rhythm_systems

    def _interfere_periodicities(self, p1: int, p2: int) -> List[float]:
        """
        Interfere two periodicities to generate a resultant rhythmic pattern.
        Based on Schillinger's concept of interference.
        """
        lcm = self._lcm(p1, p2)
        pattern = []
        for i in range(lcm):
            duration = 1 / lcm  # Simplistic division, can be enhanced based on specific rules
            pattern.append(duration)
        logger.debug(f"Interfered periodicities {p1} and {p2} to create pattern: {pattern}")
        return pattern

    def _lcm(self, a: int, b: int) -> int:
        """
        Calculate the Least Common Multiple of two integers.
        """
        from math import gcd
        return abs(a*b) // gcd(a, b) if a and b else 0

    def _generate_groupings(self) -> Dict:
        """
        Generate rhythmic groupings based on Cooper and Meyer's theory.
        Utilizes grouping principles to categorize rhythmic patterns.
        """
        groupings = {}
        for pattern_str, details in self.rhythm_systems.items():
            grouping_type = self._determine_cooper_meyer_grouping(details['resultant'])
            groupings[pattern_str] = grouping_type
            logger.debug(f"Pattern {pattern_str} classified as grouping type: {grouping_type}")
        return groupings

    def _determine_cooper_meyer_grouping(self, pattern: List[float]) -> str:
        """
        Determine the grouping type based on Cooper and Meyer's grouping principles.
        """
        # Example implementation based on grouping strength and hierarchical structure
        total = sum(pattern)
        if total == 1:
            return "simple"
        elif total < 1:
            return "complex"
        else:
            return "compound"

    def _determine_grouping(self, pattern: List[float]) -> str:
        """
        Determine rhythmic grouping as per Cooper and Meyer's theory.
        """
        pattern_str = self._pattern_to_str(pattern)
        return self.groupings.get(pattern_str, "simple")

    def _pattern_to_str(self, pattern: List[float]) -> str:
        """
        Convert rhythmic pattern to string representation.
        """
        return '-'.join(str(d) for d in pattern)

    def _generate_rhythmic_transformations(self, pattern: List[float]) -> List[str]:
        """
        Generate possible rhythmic transformations of a pattern based on Schillinger's transformations.
        """
        transformations = []
        # Apply rhythmic permutations, rotations, augmentations, diminutions
        # Permutations
        permutations = self._permute_rhythm(pattern)
        for perm in permutations:
            transformations.append(self._pattern_to_str(perm))
        # Rotations
        rotations = self._rotate_rhythm(pattern)
        for rot in rotations:
            transformations.append(self._pattern_to_str(rot))
        # Augmentation and Diminution as per Schillinger
        augmented = self._augment_rhythm(pattern)
        diminished = self._diminish_rhythm(pattern)
        transformations.append(self._pattern_to_str(augmented))
        transformations.append(self._pattern_to_str(diminished))
        logger.debug(f"Generated rhythmic transformations for pattern {self._pattern_to_str(pattern)}: {transformations}")
        return transformations

    def _permute_rhythm(self, pattern: List[float]) -> List[List[float]]:
        """
        Generate permutations of a rhythmic pattern.
        """
        return list(itertools.permutations(pattern))

    def _rotate_rhythm(self, pattern: List[float]) -> List[List[float]]:
        """
        Generate rotations of a rhythmic pattern (cyclic permutations).
        """
        rotations = []
        n = len(pattern)
        for i in range(1, n):
            rotation = pattern[i:] + pattern[:i]
            rotations.append(rotation)
        logger.debug(f"Generated rotations for pattern {self._pattern_to_str(pattern)}: {rotations}")
        return rotations

    def _augment_rhythm(self, pattern: List[float]) -> List[float]:
        """
        Augment the rhythmic pattern by doubling each duration.
        """
        return [d * 2 for d in pattern]

    def _diminish_rhythm(self, pattern: List[float]) -> List[float]:
        """
        Diminish the rhythmic pattern by halving each duration.
        """
        return [d / 2 for d in pattern]

    def _determine_rhythm_weight(self, current_rhythm: RhythmicPattern, next_rhythm: RhythmicPattern) -> int:
        """
        Determines the weight of transitioning from current_rhythm to next_rhythm.
        """
        # Assign higher weight to patterns that are rhythmic transformations
        if current_rhythm.accent == next_rhythm.accent:
            weight = 10
        else:
            weight = 8  # Slight preference for same accent transitions
        # Additional weight for rhythmic similarity based on Schillinger's interference
        similarity = self._compare_patterns(current_rhythm.pattern, next_rhythm.pattern)
        weight += int(similarity * 5)  # Scale similarity to weight
        logger.debug(f"Determined weight for transition from {self._pattern_to_str(current_rhythm.pattern)} to {self._pattern_to_str(next_rhythm.pattern)}: {weight}")
        return weight

    def _compare_patterns(self, pattern1: List[float], pattern2: List[float]) -> float:
        """
        Compare two rhythmic patterns and return a similarity score between 0 and 1.
        Utilizes Schillinger's concept of rhythmic similarity based on periodicities.
        """
        # Calculate similarity based on common periodicities
        set1 = set(pattern1)
        set2 = set(pattern2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        if not union:
            return 0
        similarity = len(intersection) / len(union)
        logger.debug(f"Compared patterns {self._pattern_to_str(pattern1)} and {self._pattern_to_str(pattern2)}: similarity score = {similarity}")
        return similarity

    def _set_default_meter(self) -> str:
        """
        Set the default meter based on common time signatures.
        """
        # Utilizing Schillinger's emphasis on meter in rhythmic structuring
        return "4/4"

    def _detect_motifs(self, rhythms: List[RhythmicPattern]) -> List:
        """
        Detect rhythmic motifs using Cooper and Meyer's grouping principles.
        Identifies recurring rhythmic patterns within the rhythm graph.
        """
        motifs = []
        pattern_counts = {}
        for rhythm in rhythms:
            pattern_str = self._pattern_to_str(rhythm.pattern)
            pattern_counts[pattern_str] = pattern_counts.get(pattern_str, 0) + 1
        
        for pattern, count in pattern_counts.items():
            if count > 1:
                motifs.append(pattern)
                logger.debug(f"Detected motif: {pattern} with count: {count}")
        
        return motifs

    def decide_rhythm(self, current_context):
        """
        Decide on the next rhythmic pattern based on current context and graph state.
        Integrates Schillinger's decision-making process for rhythmic selection.
        """
        if self._needs_quick_response(current_context):
            logger.info("Quick rhythm decision needed.")
            return self._quick_rhythm_decision(current_context)
        else:
            logger.info("Detailed rhythm decision needed.")
            return self._detailed_rhythm_decision(current_context)

    def _needs_quick_response(self, context):
        """
        Determine if a quick response is needed based on the context.
        """
        # Placeholder for time constraint logic
        return context.get('time_remaining', 0) < 2  # Example threshold

    def _quick_rhythm_decision(self, context):
        """
        Provide a quick rhythmic response using basic patterns.
        """
        # Use default or common rhythmic patterns influenced by Schillinger's simplicity principle
        default_pattern = [1, 1, 1, 1]  # Quarter notes in 4/4
        logger.debug(f"Quick rhythm decision made: {default_pattern}")
        return {
            'pattern': default_pattern,
            'tempo': self.tempo,
            'meter': self.meter
        }

    def _detailed_rhythm_decision(self, context):
        """
        Provide a detailed rhythmic response using full analysis.
        """
        # Analyze graph to choose a suitable rhythm based on Schillinger's comprehensive approach
        current_pattern_str = context.get('current_pattern')
        if current_pattern_str and current_pattern_str in self.graph.nodes:
            neighbors = self.graph[current_pattern_str]
            if neighbors:
                # Select neighbor with highest weight
                next_pattern_str = max(neighbors, key=lambda k: neighbors[k]['weight'])
                pattern = [float(d) for d in next_pattern_str.split('-')]
                logger.info(f"Detailed rhythm decision made: {pattern} based on current pattern: {current_pattern_str}")
                return {
                    'pattern': pattern,
                    'tempo': self.tempo,
                    'meter': self.meter
                }
        # If no suitable pattern, fallback to quick decision
        logger.warning("No suitable pattern found, falling back to quick decision.")
        return self._quick_rhythm_decision(context)
