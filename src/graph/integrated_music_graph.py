import networkx as nx
from .scale_graph import ScaleGraphBuilder
from .chord_graph import ChordGraphBuilder
from .rhythm_graph import RhythmGraphBuilder
from .motif_graph import MotifGraphBuilder
from .harmony_graph import HarmonyGraphBuilder

class IntegratedMusicGraph:
    def __init__(self):
        self.scale_builder = ScaleGraphBuilder()
        self.chord_builder = ChordGraphBuilder()
        self.rhythm_builder = RhythmGraphBuilder()
        self.motif_builder = MotifGraphBuilder()
        self.harmony_builder = HarmonyGraphBuilder()
        self.integrated_graph = nx.MultiDiGraph()

    def build_full_graph(self, scale_notes, chords, rhythms, motifs):
        # Build individual layers with advanced rules
        self.scale_builder.build_scale_graph(scale_notes)
        self.chord_builder.build_chord_graph(chords, self.scale_builder)
        self.rhythm_builder.build_rhythm_graph(rhythms)
        self.motif_builder.build_motif_graph(motifs)
        self.harmony_builder.build_harmony_graph(chords)

        # Integrate layers
        self.integrated_graph = nx.compose_all([
            self.scale_builder.get_graph(),
            self.chord_builder.get_graph(),
            self.rhythm_builder.get_graph(),
            self.motif_builder.get_graph(),
            self.harmony_builder.get_graph(),
        ])

        # Add inter-layer edges as needed with advanced relationships
        self._link_layers()

    def _link_layers(self):
        # Connect chords to rhythms
        for chord in self.chord_builder.get_graph().nodes:
            for rhythm in self.rhythm_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    chord,
                    rhythm,
                    layer='chord-rhythm',
                    weight=5
                )
        
        # Connect rhythms to motifs
        for rhythm in self.rhythm_builder.get_graph().nodes:
            for motif in self.motif_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    rhythm,
                    motif,
                    layer='rhythm-motif',
                    weight=5
                )
        
        # Connect harmony to motifs
        for chord in self.harmony_builder.get_graph().nodes:
            for motif in self.motif_builder.get_graph().nodes:
                self.integrated_graph.add_edge(
                    chord,
                    motif,
                    layer='harmony-motif',
                    weight=5
                )
        
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

    def get_integrated_graph(self) -> nx.MultiDiGraph:
        return self.integrated_graph