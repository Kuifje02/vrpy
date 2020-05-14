from networkx import DiGraph, Graph, NetworkXError
import pytest
import sys

sys.path.append("../../vrpy/")
from vrpy import VehicleRoutingProblem


#####################
# consistency tests #
#####################


def test_consistency_vrp():
    """Tests consistency of input graph."""
    G = Graph()
    with pytest.raises(TypeError):
        VehicleRoutingProblem(G)
    G = DiGraph()
    G.add_edge("Source", 1, cost=0)
    with pytest.raises(KeyError) and pytest.raises(NetworkXError):
        VehicleRoutingProblem(G)
    G.add_edge(1, "Sink")
    with pytest.raises(KeyError):
        VehicleRoutingProblem(G)
    G.edges[1, "Sink"]["cost"] = 1
    G.add_edge("Sink", 2, cost=3)
    with pytest.raises(NetworkXError):
        VehicleRoutingProblem(G)
    G.remove_edge("Sink", 2)
    with pytest.raises(TypeError):
        VehicleRoutingProblem(G, num_stops=3.5)
    with pytest.raises(TypeError):
        VehicleRoutingProblem(G, load_capacity=-10)
    with pytest.raises(TypeError):
        VehicleRoutingProblem(G, duration=0)


def test_consistency_parameters():
    """Checks if solving parameters are consistent."""
    G = DiGraph()
    G.add_edge("Source", "Sink", cost=1)
    prob = VehicleRoutingProblem(G, pickup_delivery=True)
    # pickup delivery requires cspy=False
    with pytest.raises(NotImplementedError):
        prob.solve()
    # pickup delivery requires pricing_strategy="Exact"
    with pytest.raises(ValueError):
        prob.solve(cspy=False, pricing_strategy="Stops")
    # pickup delivery expects at least one request
    with pytest.raises(KeyError):
        prob.solve(cspy=False, pricing_strategy="Exact")
