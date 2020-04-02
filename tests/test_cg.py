import sys

sys.path.append("../")
sys.path.append("../vrpy/")
from vrpy import main


def test_main_lp():
    """Tests column generation procedure on toy graph with LP"""
    G = main.create_graph()
    G.remove_node(5)
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes)
    assert best_value == 60


def test_main_cspy():
    """Tests column generation procedure on toy graph with cspy"""
    G = main.create_graph()
    G.remove_node(5)
    initial_routes = main.initialize_routes(G)
    best_value = main.main(G, initial_routes, cspy=True)
    assert best_value == 60
