from .base_graph import BaseGraph
from typing import List
from models import Motif
import logging

logger = logging.getLogger(__name__)

class MotifGraphBuilder(BaseGraph):
    def build_motif_graph(self, motifs: List[Motif]):
        logger.info(f"Building motif graph with {len(motifs)} motifs.")
        for motif in motifs:
            logger.debug(f"Adding node: {motif.name} with contour: {motif.contour}, length: {motif.length}, similarity: {motif.similarity}")
            self.add_node(
                motif.name,
                contour=motif.contour,
                length=motif.length,
                similarity=motif.similarity
            )
        
        # Define motif transitions based on similarity and contour
        logger.info("Defining motif transitions based on similarity and contour.")
        for current_motif in motifs:
            for next_motif in motifs:
                if current_motif == next_motif:
                    continue
                similarity = self._calculate_similarity(current_motif, next_motif)
                weight = int(current_motif.similarity * 10)  # Scale similarity to weight
                logger.debug(f"Adding edge from {current_motif.name} to {next_motif.name} with similarity: {similarity} and weight: {weight}")
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
            logger.debug(f"Motifs {motif1.name} and {motif2.name} are identical in contour.")
            return 1.0
        else:
            logger.debug(f"Motifs {motif1.name} and {motif2.name} differ in contour.")
            return 0.5  # Less similarity if contours differ