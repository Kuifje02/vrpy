from networkx import DiGraph, Graph, NetworkXError
import pytest
import sys

sys.path.append("../")
from vrpy.vrp import VehicleRoutingProblem

#####################
# consistency tests #
#####################


def test_check_vrp():
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
    with pytest.raises(NetworkXError):
        VehicleRoutingProblem(G)
    G.remove_edge("Sink", 2)


def test_check_arguments():
    G = DiGraph()
    G.add_edge("Source", "Sink", cost=1)
    with pytest.raises(TypeError):
        prob = VehicleRoutingProblem(G, num_stops=3.5)
        prob.solve()
    with pytest.raises(TypeError):
        prob = VehicleRoutingProblem(G, load_capacity=-10)
        prob.solve()
    with pytest.raises(TypeError):
        prob = VehicleRoutingProblem(G, duration=-1)
        prob.solve()
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G)
        prob.solve(pricing_strategy="Best")


def test_consistency_parameters():
    """Checks if solving parameters are consistent."""
    G = DiGraph()
    G.add_edge("Source", "Sink", cost=1)
    prob = VehicleRoutingProblem(G, pickup_delivery=True)
    # pickup delivery expects at least one request
    with pytest.raises(KeyError):
        prob.solve(cspy=False, pricing_strategy="Exact")


def test_heuristic_only_consistency():
    """Checks is error is raised if heuristic_only is active with wrong arguments"""
    G = DiGraph()
    G.add_edge("Source", "Sink", cost=1)
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, time_windows=True)
        prob.solve(heuristic_only=True)
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, mixed_fleet=True)
        prob.solve(heuristic_only=True)
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, distribution_collection=True)
        prob.solve(heuristic_only=True)
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, periodic=True)
        prob.solve(heuristic_only=True)


def test_mixed_fleet_consistency():
    """Checks if mixed fleet arguments are consistent."""
    G = DiGraph()
    G.add_edge("Source", "Sink", cost=1)
    with pytest.raises(TypeError):
        prob = VehicleRoutingProblem(G, mixed_fleet=True, load_capacity=[2, 4])
        prob.solve()
    G.edges["Source", "Sink"]["cost"] = [1, 2]
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G,
                                     mixed_fleet=True,
                                     load_capacity=[2, 4],
                                     fixed_cost=[4])
        prob.solve()


def test_feasibility_check():
    """Tests feasibility checks."""
    G = DiGraph()
    G.add_edge("Source", 1, cost=1, time=1)
    G.add_edge(1, "Sink", cost=1, time=1)
    G.nodes[1]["demand"] = 2
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, load_capacity=1)
        prob.solve()
    with pytest.raises(ValueError):
        prob = VehicleRoutingProblem(G, duration=1)
        prob.solve()


def test_locked_routes_check():
    """Tests if locked routes check."""
    G = DiGraph()
    G.add_edge("Source", 1, cost=1)
    G.add_edge(1, "Sink", cost=1)
    G.nodes[1]["demand"] = 2
    prob = VehicleRoutingProblem(G)
    with pytest.raises(ValueError):
        prob.solve(preassignments=[[1, 2]])
