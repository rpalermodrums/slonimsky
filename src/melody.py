import random
import networkx as nx
from typing import List
from models import NoteEvent

class MelodyGenerator:
    def __init__(self, integrated_graph: nx.MultiDiGraph):
        self.graph = integrated_graph

    def generate_melody(self, start_note: str, length: int) -> List[str]:
        """
        Generates a melody using a weighted random walk through the graph.

        :param start_note: Starting note for the melody.
        :param length: Desired length of the melody.
        :return: List of note names representing the melody.
        """
        melody = [start_note]
        current_note = start_note

        for _ in range(length - 1):
            successors = list(self.graph.successors(current_note))
            if not successors:
                break
            next_note = self._select_next_note(current_note, successors)
            melody.append(next_note)
            current_note = next_note

        return melody

    def _select_next_note(self, current_note: str, successors: List[str]) -> str:
        """
        Selects the next note based on weighted probabilities.

        :param current_note: Current note in the melody.
        :param successors: Possible next notes.
        :return: Selected next note.
        """
        edges = self.graph.get_edge_data(current_note, None)
        if not edges:
            return current_note  # No transition available

        weights = []
        notes = []
        for to_node in successors:
            # Consider multiple edges (layers)
            edge_weights = [attr.get('weight', 1) for _, _, attr in self.graph.edges(current_note, to_node, data=True)]
            total_weight = sum(edge_weights)
            weights.append(total_weight)
            notes.append(to_node)
        
        # Weighted random selection
        total = sum(weights)
        if total == 0:
            return current_note  # Avoid division by zero
        r = random.uniform(0, total)
        upto = 0
        for note, weight in zip(notes, weights):
            if upto + weight >= r:
                return note
            upto += weight
        return notes[-1]

    def generate_melody_dijkstra(self) -> List[str]:
        """
        Generates a melody using Dijkstra's algorithm, favoring higher weights.

        :return: List of note names representing the melody.
        """
        start_nodes = [node for node, attr in self.graph.nodes(data=True) if attr.get('functional_role') == 'tonic']
        end_nodes = [node for node, attr in self.graph.nodes(data=True) if attr.get('functional_role') == 'tonic']

        best_melody = []
        best_weight = float('-inf')

        for start_node in start_nodes:
            for end_node in end_nodes:
                try:
                    # Invert weights for Dijkstra to find the path with the highest total weight
                    path = nx.dijkstra_path(
                        self.graph,
                        start_node,
                        end_node,
                        weight=lambda u, v, d: -d.get('weight', 1)
                    )
                    path_weight = sum(d.get('weight', 1) for u, v, d in zip(path, path[1:], path[:-1]))
                    if path_weight > best_weight:
                        best_weight = path_weight
                        best_melody = path
                except nx.NetworkXNoPath:
                    continue

        if not best_melody:
            raise ValueError("No valid melody path found.")

        return best_melody

    def generate_melody_random_walk(self) -> List[str]:
        """
        Generates a melody using a weighted random walk through the graph.

        :return: List of note names representing the melody.
        """
        times = sorted(set(node[1] for node in self.graph.nodes))
        current_time = times[0]
        melody = []

        current_nodes = [node for node in self.graph.nodes if node[1] == current_time]
        if not current_nodes:
            raise ValueError("No start nodes available.")

        current_node = random.choice(current_nodes)
        melody.append(current_node[0])

        for time in times[1:]:
            successors = list(self.graph.successors(current_node))
            if not successors:
                break
            weights = [self.graph[current_node][succ]['weight'] for succ in successors]
            total = sum(weights)
            if total == 0:
                next_note = current_node[0]
            else:
                probabilities = [w / total for w in weights]
                next_note = random.choices(successors, weights=probabilities, k=1)[0]
            melody.append(next_note)
            current_node = next_note

        return melody
    