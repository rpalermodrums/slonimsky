import networkx as nx
import logging
from .scale_graph import ScaleGraphBuilder
from .chord_graph import ChordGraphBuilder
from .rhythm_graph import RhythmGraphBuilder
from .motif_graph import MotifGraphBuilder
from .harmony_graph import HarmonyGraphBuilder

logger = logging.getLogger(__name__)

class IntegratedMusicGraph:
    def __init__(self):
        logger.info("Initializing IntegratedMusicGraph...")
        self.scale_builder = ScaleGraphBuilder()
        self.chord_builder = ChordGraphBuilder()
        self.rhythm_builder = RhythmGraphBuilder()
        self.motif_builder = MotifGraphBuilder()
        self.harmony_builder = HarmonyGraphBuilder()
        self.integrated_graph = nx.MultiDiGraph()
        logger.info("IntegratedMusicGraph initialized.")

    def build_full_graph(self, scale_notes, chords, rhythms, motifs):
        logger.info("Building full integrated music graph...")
        # Build individual layers with advanced rules
        self.scale_builder.build_scale_graph(scale_notes)
        logger.debug("Scale graph built.")
        self.chord_builder.build_chord_graph(chords, self.scale_builder)
        logger.debug("Chord graph built.")
        self.rhythm_builder.build_rhythm_graph(rhythms)
        logger.debug("Rhythm graph built.")
        self.motif_builder.build_motif_graph(motifs)
        logger.debug("Motif graph built.")
        self.harmony_builder.build_harmony_graph(chords)
        logger.debug("Harmony graph built.")

        # Integrate layers
        self.integrated_graph = nx.compose_all([
            self.scale_builder.get_graph(),
            self.chord_builder.get_graph(),
            self.rhythm_builder.get_graph(),
            self.motif_builder.get_graph(),
            self.harmony_builder.get_graph(),
        ])
        logger.info("All layers integrated into a single graph.")

        # Add inter-layer edges as needed with advanced relationships
        self._link_layers()

    def _link_layers(self):
        logger.info("Linking layers...")
        # Connect chords to rhythms
        for chord in self.chord_builder.get_graph().nodes:
            for rhythm in self.rhythm_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    chord,
                    rhythm,
                    layer='chord-rhythm',
                    weight=5
                )
                logger.debug(f"Added edge from chord '{chord}' to rhythm '{rhythm}'.")

        # Connect rhythms to motifs
        for rhythm in self.rhythm_builder.get_graph().nodes:
            for motif in self.motif_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    rhythm,
                    motif,
                    layer='rhythm-motif',
                    weight=5
                )
                logger.debug(f"Added edge from rhythm '{rhythm}' to motif '{motif}'.")

        # Connect harmony to motifs
        for chord in self.harmony_builder.get_graph().nodes:
            for motif in self.motif_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    chord,
                    motif,
                    layer='harmony-motif',
                    weight=5
                )
                logger.debug(f"Added edge from harmony '{chord}' to motif '{motif}'.")

        # Additional inter-layer connections based on advanced music theory
        # Example: Connect modal interchange chords to their functional roles
        for chord in self.chord_builder.get_graph().nodes(data=True):
            if chord[1].get('modal_interchange'):
                self.integrated_graph.add_edge(
                    chord[0],
                    chord[0],
                    layer='modal-home',
                    weight=3
                )
                logger.debug(f"Added modal-home edge for chord '{chord[0]}'.")

    def get_integrated_graph(self) -> nx.MultiDiGraph:
        logger.info("Retrieving integrated graph.")
        return self.integrated_graph