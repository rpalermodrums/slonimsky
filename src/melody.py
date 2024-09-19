import random
import networkx as nx
from typing import List
import logging
from models import NoteEvent

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MelodyGenerator:
    def __init__(self, integrated_graph: nx.MultiDiGraph):
        self.graph = integrated_graph
        logger.debug("MelodyGenerator initialized with graph: %s", integrated_graph)

    def generate_melody(self, start_note: str, length: int) -> List[str]:
        """
        Generates a melody using a weighted random walk through the graph.

        :param start_note: Starting note for the melody.
        :param length: Desired length of the melody.
        :return: List of note names representing the melody.
        """
        melody = [start_note]
        current_note = start_note
        logger.info("Generating melody starting with note: %s", start_note)

        for _ in range(length - 1):
            successors = list(self.graph.successors(current_note))
            logger.debug("Current note: %s, Successors: %s", current_note, successors)
            if not successors:
                logger.warning("No successors found for note: %s", current_note)
                break
            next_note = self._select_next_note(current_note, successors)
            melody.append(next_note)
            current_note = next_note
            logger.debug("Next note selected: %s", next_note)

        logger.info("Generated melody: %s", melody)
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
            logger.warning("No edges found for current note: %s", current_note)
            return current_note  # No transition available

        weights = []
        notes = []
        for to_node in successors:
            # Consider multiple edges (layers)
            edge_weights = [attr.get('weight', 1) for _, _, attr in self.graph.edges(current_note, to_node, data=True)]
            total_weight = sum(edge_weights)
            weights.append(total_weight)
            notes.append(to_node)
            logger.debug("Edge weights for %s to %s: %s, Total weight: %d", current_note, to_node, edge_weights, total_weight)
        
        # Weighted random selection
        total = sum(weights)
        logger.debug("Total weights: %d", total)
        if total == 0:
            logger.warning("Total weight is zero, returning current note: %s", current_note)
            return current_note  # Avoid division by zero
        r = random.uniform(0, total)
        upto = 0
        for note, weight in zip(notes, weights):
            if upto + weight >= r:
                logger.debug("Selected note: %s with weight: %d", note, weight)
                return note
            upto += weight
        logger.debug("Returning last note: %s", notes[-1])
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

        logger.info("Starting Dijkstra's melody generation.")
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
                    logger.debug("Path found: %s with weight: %d", path, path_weight)
                    if path_weight > best_weight:
                        best_weight = path_weight
                        best_melody = path
                        logger.info("New best melody found: %s with weight: %d", best_melody, best_weight)
                except nx.NetworkXNoPath:
                    logger.warning("No path found from %s to %s", start_node, end_node)
                    continue

        if not best_melody:
            logger.error("No valid melody path found.")
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
        logger.info("Starting random walk melody generation.")

        current_nodes = [node for node in self.graph.nodes if node[1] == current_time]
        if not current_nodes:
            logger.error("No start nodes available.")
            raise ValueError("No start nodes available.")

        current_node = random.choice(current_nodes)
        melody.append(current_node[0])
        logger.debug("Starting node for random walk: %s", current_node[0])

        for time in times[1:]:
            successors = list(self.graph.successors(current_node))
            logger.debug("Current node: %s, Time: %s, Successors: %s", current_node, time, successors)
            if not successors:
                logger.warning("No successors found for node: %s", current_node)
                break
            weights = [self.graph[current_node][succ]['weight'] for succ in successors]
            total = sum(weights)
            if total == 0:
                next_note = current_node[0]
                logger.warning("Total weight is zero, staying on current node: %s", current_node[0])
            else:
                probabilities = [w / total for w in weights]
                next_note = random.choices(successors, weights=probabilities, k=1)[0]
            melody.append(next_note)
            current_node = next_note
            logger.debug("Next note selected: %s", next_note)

        logger.info("Generated random walk melody: %s", melody)
        return melody
