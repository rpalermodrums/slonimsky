# src/graph/motif_graph.py
from .base_graph import BaseGraph
from typing import List
from models import Motif

class MotifGraphBuilder(BaseGraph):
    def build_motif_graph(self, motifs: List[Motif]):
        for motif in motifs:
            self.add_node(
                motif.name,
                contour=motif.contour,
                length=motif.length,
                similarity=motif.similarity
            )
        
        # Define motif transitions based on similarity and contour
        for current_motif in motifs:
            for next_motif in motifs:
                if current_motif == next_motif:
                    continue
                similarity = self._calculate_similarity(current_motif, next_motif)
                weight = int(current_motif.similarity * 10)  # Scale similarity to weight
                self.add_edge(
                    current_motif.name,
                    next_motif.name,
                    similarity=similarity,
                    weight=weight
                )

    def _calculate_similarity(self, motif1: Motif, motif2: Motif) -> float:
        """
        Calculates similarity between two motifs based on their contours.
        """
        if motif1.contour == motif2.contour:
            return 1.0
        else:
            return 0.5  # Less similarity if contours differ