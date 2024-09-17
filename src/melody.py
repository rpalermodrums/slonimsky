import random
from typing import List

import networkx as nx

class MelodyGenerator:
    def __init__(self, graph: nx.DiGraph):
        """
        Initializes the MelodyGenerator with a given NetworkX graph.

        :param graph: Directed graph representing musical transitions.
        """
        self.graph = graph

    def generate_melody_dijkstra(self) -> List[str]:
        """
        Generates a melody using Dijkstra's algorithm, favoring higher weights.

        :return: List of note names representing the melody.
        """
        times = sorted(set(node[1] for node in self.graph.nodes))
        start_time = times[0]
        end_time = times[-1]
        start_nodes = [node for node in self.graph.nodes if node[1] == start_time]
        end_nodes = [node for node in self.graph.nodes if node[1] == end_time]

        if not start_nodes or not end_nodes:
            raise ValueError("Graph does not contain valid start or end nodes for melody generation.")

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
                        weight=lambda u, v, d: -d['weight']
                    )
                    path_weight = sum(self.graph[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                    if path_weight > best_weight:
                        best_weight = path_weight
                        best_melody = [node[0] for node in path]
                except nx.NetworkXNoPath:
                    continue

        if not best_melody:
            raise RuntimeError("Failed to generate a melody. No valid paths found.")

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
            probabilities = [w / total for w in weights]
            current_node = random.choices(successors, weights=probabilities, k=1)[0]
            melody.append(current_node[0])

        return melody