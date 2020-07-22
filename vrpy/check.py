from networkx import DiGraph, shortest_path, NetworkXError, has_path
import logging
from time import time

from .greedy import Greedy
from .master_solve_pulp import MasterSolvePulp
from .subproblem_lp import SubProblemLP
from .subproblem_cspy import SubProblemCSPY
from .subproblem_greedy import SubProblemGreedy
from .clarke_wright import ClarkeWright, RoundTrip
from .schedule import Schedule
from .main import VehicleRoutingProblem


def check_arguments(prob: VehicleRoutingProblem = None):
    """Checks if arguments are consistent."""

    #if prob is None raise instance
    if prob == None:
        raise ValueError("VRPy instance is None")

    # If num_stops/load_capacity/duration are not integers
    if prob.num_stops and (not isinstance(prob.num_stops, int)
                           or prob.num_stops <= 0):
        raise TypeError("Maximum number of stops must be positive integer.")
    if prob.load_capacity:
        for value in prob.load_capacity:
            if not isinstance(value, int) or value <= 0:
                raise TypeError("Load capacity must be positive integer.")
    if prob.duration and (not isinstance(prob.duration, int)
                          or prob.duration < 0):
        raise TypeError("Maximum duration must be positive integer.")
    strategies = [
        "Exact",
        "BestEdges1",
        "BestEdges2",
        "BestPaths",
    ]
    if prob._pricing_strategy not in strategies:
        raise ValueError(
            "Pricing strategy %s is not valid. Pick one among %s" %
            (prob._pricing_strategy, strategies))
    if prob.mixed_fleet:
        if prob.load_capacity and prob.num_vehicles:
            if not len(prob.load_capacity) == len(prob.num_vehicles):
                raise ValueError(
                    "Input arguments load_capacity and num_vehicles must have same dimension."
                )
        if prob.load_capacity and prob.fixed_cost:
            if not len(prob.load_capacity) == len(prob.fixed_cost):
                raise ValueError(
                    "Input arguments load_capacity and fixed_cost must have same dimension."
                )
        if prob.num_vehicles and prob.fixed_cost:
            if not len(prob.num_vehicles) == len(prob.fixed_cost):
                raise ValueError(
                    "Input arguments num_vehicles and fixed_cost must have same dimension."
                )
        for (i, j) in prob.G.edges():
            if not isinstance(prob.G.edges[i, j]["cost"], list):
                raise TypeError(
                    "Cost attribute for edge (%s,%s) should be of type list")
            if len(prob.G.edges[i, j]["cost"]) != prob._vehicle_types:
                raise ValueError(
                    "Cost attribute for edge (%s,%s) has dimension %s, should have dimension %s."
                    % (i, j, len(
                        prob.G.edges[i, j]["cost"]), prob._vehicle_types))


def check_vrp(prob: VehicleRoutingProblem = None):
    """Checks if graph is well defined."""

    #if prob is None raise instance
    if prob == None:
        raise ValueError("VRPy instance is None")

    # if G is not a DiGraph
    if not isinstance(prob.G, DiGraph):
        raise TypeError(
            "Input graph must be of type networkx.classes.digraph.DiGraph.")
    for v in ["Source", "Sink"]:
        # If Source or Sink is missing
        if v not in prob.G.nodes():
            raise KeyError("Input graph requires Source and Sink nodes.")
        # If Source has incoming edges
        if len(list(prob.G.predecessors("Source"))) > 0:
            raise NetworkXError("Source must have no incoming edges.")
        # If Sink has outgoing edges
        if len(list(prob.G.successors("Sink"))) > 0:
            raise NetworkXError("Sink must have no outgoing edges.")
    # Roundtrips should always be possible
    # Missing edges are added with a high cost
    for v in prob.G.nodes():
        if v not in ["Source", "Sink"]:
            if v not in prob.G.successors("Source"):
                logger.warning("Source not connected to %s" % v)
                prob.G.add_edge("Source", v, cost=1e10)
            if v not in prob.G.predecessors("Sink"):
                logger.warning("%s not connected to Sink" % v)
                prob.G.add_edge(v, "Sink", cost=1e10)
    # If graph is disconnected
    if not has_path(prob.G, "Source", "Sink"):
        raise NetworkXError("Source and Sink are not connected.")
    # If cost is missing
    for (i, j) in prob.G.edges():
        if "cost" not in prob.G.edges[i, j]:
            raise KeyError("Edge (%s,%s) requires cost attribute" % (i, j))


def check_initial_routes(prob: VehicleRoutingProblem = None):
    """
    Checks if initial routes are consistent.
    TO DO : check if it is entirely feasible depending on VRP type.
    One way of doing it : run the subproblem by fixing variables corresponding to initial solution.
    """

    #if prob is None raise instance
    if prob == None:
        raise ValueError("VRPy instance is None")

    # Check if routes start at Sink and end at Node
    for route in prob._initial_routes:
        if route[0] != "Source" or route[-1] != "Sink":
            raise ValueError("Route %s must start at Source and end at Sink" %
                             route)
    # Check if every node is in at least one route
    for v in prob.G.nodes():
        if v not in ["Source", "Sink"]:
            node_found = 0
            for route in prob._initial_routes:
                if v in route:
                    node_found += 1
            if node_found == 0:
                raise KeyError("Node %s missing from initial solution." % v)
    # Check if edges from initial solution exist and have cost attribute
    for route in prob._initial_routes:
        edges = list(zip(route[:-1], route[1:]))
        for (i, j) in edges:
            if (i, j) not in prob.G.edges():
                raise KeyError("Edge (%s,%s) in route %s missing in graph." %
                               (i, j, route))
            if "cost" not in prob.G.edges[i, j]:
                raise KeyError("Edge (%s,%s) has no cost attribute." % (i, j))


def check_consistency(prob: VehicleRoutingProblem = None):
    """Raises errors if options are inconsistent with parameters."""

    #if prob is None raise instance
    if prob == None:
        raise ValueError("VRPy instance is None")

    # pickup delivery requires cspy=False
    if prob._cspy and prob.pickup_delivery:
        raise NotImplementedError(
            "pickup_delivery option requires cspy=False.")
    # pickup delivery requires pricing_stragy="Exact"
    if prob.pickup_delivery and prob._pricing_strategy != "Exact":
        prob._pricing_strategy = "Exact"
        logger.warning("Pricing_strategy changed to 'Exact'.")
    # pickup delivery expects at least one request
    if prob.pickup_delivery:
        request = False
        for v in prob.G.nodes():
            if "request" in prob.G.nodes[v]:
                request = True
                break
        if not request:
            raise KeyError(
                "pickup_delivery option expects at least one request.")


def check_feasibility(prob: VehicleRoutingProblem = None):
    """Checks basic problem feasibility."""

    #if prob is None raise instance
    if prob == None:
        raise ValueError("VRPy instance is None")

    if prob.load_capacity:
        for v in prob.G.nodes():
            if prob.G.nodes[v]["demand"] > max(prob.load_capacity):
                raise ValueError(
                    "Demand %s at node %s larger than max capacity %s." %
                    (prob.G.nodes[v]["demand"], v, max(prob.load_capacity)))
    if prob.duration:
        for v in prob.G.nodes():
            if v not in ["Source", "Sink"]:
                round_trip_duration = (prob.G.nodes[v]["service_time"] +
                                       prob.G.edges["Source", v]["time"] +
                                       prob.G.edges[v, "Sink"]["time"])
                if round_trip_duration > prob.duration:
                    raise ValueError(
                        "Node %s not reachable: duration of path [Source,%s,Sink], %s, is larger than max duration %s."
                        % (v, v, round_trip_duration, prob.duration))