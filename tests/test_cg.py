import networkx as nx
import sys

sys.path.append("../vrpy")
from vrpy.vrpy import main


def test_main():
    """Tests column generation procedure on toy graph"""
    G = create_graph()
    initial_routes = initialize_routes(G)
    best_value = main.main(G, initial_routes)
    assert best_value == 60


def create_graph():
    """Creates a toy graph
    
    Returns:
        G -- A networkx DiGraph
    """
    G = nx.DiGraph()
    for v in [1, 2, 3, 4]:
        G.add_edge("Source", v, cost=10)
        G.add_edge(v, "Sink", cost=10)
    G.add_edge(1, 2, cost=10)
    G.add_edge(2, 3, cost=15)
    G.add_edge(3, 4, cost=10)
    return G


def initialize_routes(G):
    """Sets the initial routes for first iteration
    
    Arguments:
        G {networkx DiGraph} -- The graph representing the network
    
    Returns:
        routes -- A list of initial routes as network DiGraphs
    """
    routes = []
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            route = nx.DiGraph(name=v, cost=20)
            route.add_edge("Source", v, cost=10)
            route.add_edge(v, "Sink", cost=10)
            routes.append(route)
    return routes
