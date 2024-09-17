from dataclasses import dataclass, field
from typing import List, Dict, Any
from collections import defaultdict

import networkx as nx

@dataclass
class Transition:
    to_note: str
    chords: List[str]           # Chords in which this transition is valid
    beat_positions: List[str]   # 'strong', 'weak'
    type: str                   # 'consonant' or 'dissonant'

@dataclass
class Chord:
    name: str
    notes: List[str]

@dataclass
class ImprovisationGraph:
    key_center: str
    chords: List[Chord]
    beat_strengths: List[str] = field(default_factory=lambda: ['strong', 'weak'])
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def add_note(self, note: str):
        if not self.graph.has_node(note):
            self.graph.add_node(note)

    def add_transition(self, from_note: str, transition: Transition):
        self.add_note(from_note)
        self.add_note(transition.to_note)
        # Add edge with attributes
        if self.graph.has_edge(from_note, transition.to_note):
            # If edge exists, append new attributes without duplicates
            existing = self.graph[from_note][transition.to_note]
            existing['chords'] = list(set(existing['chords'] + transition.chords))
            existing['beat_positions'] = list(set(existing['beat_positions'] + transition.beat_positions))
            if transition.type not in existing['type']:
                existing['type'] += f", {transition.type}"
        else:
            self.graph.add_edge(from_note, transition.to_note,
                                chords=transition.chords.copy(),
                                beat_positions=transition.beat_positions.copy(),
                                type=transition.type)

    def get_transitions(self, from_note: str) -> List[Transition]:
        if not self.graph.has_node(from_note):
            return []
        transitions = []
        for to_note in self.graph.successors(from_note):
            attrs = self.graph[from_note][to_note]
            transition = Transition(
                to_note=to_note,
                chords=attrs.get('chords', []),
                beat_positions=attrs.get('beat_positions', []),
                type=attrs.get('type', '')
            )
            transitions.append(transition)
        return transitions

    def display_graph(self):
        for from_note in self.graph.nodes:
            transitions = self.get_transitions(from_note)
            for t in transitions:
                print(f"{from_note} --({t.chords}, {t.beat_positions}, {t.type})--> {t.to_note}")
