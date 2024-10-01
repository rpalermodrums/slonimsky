import networkx as nx
from typing import Any, Dict

class BaseGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node: Any, **attrs):
        self.graph.add_node(node, **attrs)

    def add_edge(self, from_node: Any, to_node: Any, **attrs):
        self.graph.add_edge(from_node, to_node, **attrs)

    def get_graph(self) -> nx.DiGraph:
        return self.graph