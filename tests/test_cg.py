import networkx as nx
import sys

sys.path.append("../vrpy")
from vrpy.vrpy import main


def test_main():
    """Tests column generation procedure on toy graph"""
    G = main.create_graph()
    G.remove_node(5)
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes)
    assert best_value == 60
