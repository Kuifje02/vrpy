import sys

sys.path.append("../vrpy")
from vrpy.vrpy import main


def test_missing_node():
    """Tests column generation procedure on toy graph"""
    G = main.create_graph()
    G.remove_node(5)
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes)
    assert best_value == 60


def test_sub_cspy():
    """Tests column generation procedure on toy graph"""
    G = main.create_graph()
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes, cspy=True)
    assert best_value == 80


def test_sub_pulp():
    """Tests column generation procedure on toy graph"""
    G = main.create_graph()
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes, max_load=True)
    assert best_value == 80
