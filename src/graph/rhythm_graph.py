# src/graph/rhythm_graph.py
from .base_graph import BaseGraph
from typing import List
from models import RhythmicPattern

class RhythmGraphBuilder(BaseGraph):
    def build_rhythm_graph(self, rhythms: List[RhythmicPattern]):
        for rhythm in rhythms:
            self.add_node(
                rhythm.pattern,
                tempo=rhythm.tempo,
                accent=rhythm.accent
            )
        
        # Define rhythmic transitions based on rhythm types and accents
        for current_rhythm in rhythms:
            for next_rhythm in rhythms:
                if current_rhythm == next_rhythm:
                    continue
                weight = self._determine_rhythm_weight(current_rhythm, next_rhythm)
                self.add_edge(
                    current_rhythm.pattern,
                    next_rhythm.pattern,
                    weight=weight
                )

    def _determine_rhythm_weight(self, current_rhythm: RhythmicPattern, next_rhythm: RhythmicPattern) -> int:
        """
        Determines the weight of transitioning from current_rhythm to next_rhythm based on their accents.
        """
        if current_rhythm.accent == next_rhythm.accent:
            return 10
        else:
            return 8  # Slight preference for same accent transitions