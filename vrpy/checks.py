"""Functions to check input types and consistency.
"""
import logging

from numpy.random import RandomState
from networkx import DiGraph, NetworkXError, has_path

logger = logging.getLogger(__name__)


def check_arguments(num_stops: int = None,
                    load_capacity: list = None,
                    duration: int = None,
                    pricing_strategy: str = None,
                    mixed_fleet: bool = None,
                    fixed_cost: bool = None,
                    G: DiGraph = None,
                    vehicle_types: int = None,
                    num_vehicles: list = None):
    """Checks if arguments are consistent."""

    # If num_stops/load_capacity/duration are not integers
    if num_stops and (not isinstance(num_stops, int) or num_stops <= 0):
        raise TypeError("Maximum number of stops must be positive integer.")
    if load_capacity:
        for value in load_capacity:
            if not isinstance(value, int) or value <= 0:
                raise TypeError("Load capacity must be positive integer.")
    if duration and (not isinstance(duration, int) or duration < 0):
        raise TypeError("Maximum duration must be positive integer.")
    strategies = ["Exact", "BestEdges1", "BestEdges2", "BestPaths", "Hyper"]
    if pricing_strategy not in strategies:
        raise ValueError("Pricing strategy %s is not valid. Pick one among %s" %
                         (pricing_strategy, strategies))
    if mixed_fleet:
        if (load_capacity and num_vehicles and
                len(load_capacity) != len(num_vehicles)):
            raise ValueError(
                "Input arguments load_capacity and num_vehicles must have same dimension."
            )
        if (load_capacity and fixed_cost and
                len(load_capacity) != len(fixed_cost)):
            raise ValueError(
                "Input arguments load_capacity and fixed_cost must have same dimension."
            )
        if (num_vehicles and fixed_cost and
                len(num_vehicles) != len(fixed_cost)):
            raise ValueError(
                "Input arguments num_vehicles and fixed_cost must have same dimension."
            )
        for (i, j) in G.edges():
            if not isinstance(G.edges[i, j]["cost"], list):
                raise TypeError(
                    "Cost attribute for edge (%s,%s) should be of type list")
            if len(G.edges[i, j]["cost"]) != vehicle_types:
                raise ValueError(
                    "Cost attribute for edge (%s,%s) has dimension %s, should have dimension %s."
                    % (i, j, len(G.edges[i, j]["cost"]), vehicle_types))


def check_vrp(G: DiGraph = None):
    """Checks if graph is well defined."""

    # if G is not a DiGraph
    if not isinstance(G, DiGraph):
        raise TypeError(
            "Input graph must be of type networkx.classes.digraph.DiGraph.")
    for v in ["Source", "Sink"]:
        # If Source or Sink is missing
        if v not in G.nodes():
            raise KeyError("Input graph requires Source and Sink nodes.")
        # If Source has incoming edges
        if len(list(G.predecessors("Source"))) > 0:
            raise NetworkXError("Source must have no incoming edges.")
        # If Sink has outgoing edges
        if len(list(G.successors("Sink"))) > 0:
            raise NetworkXError("Sink must have no outgoing edges.")
    # Roundtrips should always be possible
    # Missing edges are added with a high cost
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            if v not in G.successors("Source"):
                logger.warning("Source not connected to %s" % v)
                G.add_edge("Source", v, cost=1e10)
            if v not in G.predecessors("Sink"):
                logger.warning("%s not connected to Sink" % v)
                G.add_edge(v, "Sink", cost=1e10)
    # If graph is disconnected
    if not has_path(G, "Source", "Sink"):
        raise NetworkXError("Source and Sink are not connected.")
    # If cost is missing
    for (i, j) in G.edges():
        if "cost" not in G.edges[i, j]:
            raise KeyError("Edge (%s,%s) requires cost attribute" % (i, j))


def check_initial_routes(initial_routes: list = None, G: DiGraph = None):
    """
    Checks if initial routes are consistent.
    TODO : check if it is entirely feasible depending on VRP type.
    One way of doing it : run the subproblem by fixing variables corresponding to initial solution.
    """

    # Check if routes start at Sink and end at Node

    for route in initial_routes:
        if route[0] != "Source" or route[-1] != "Sink":
            raise ValueError("Route %s must start at Source and end at Sink" %
                             route)
    # Check if every node is in at least one route
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            node_found = 0
            for route in initial_routes:
                if v in route:
                    node_found += 1
            if node_found == 0:
                raise KeyError("Node %s missing from initial solution." % v)
    # Check if edges from initial solution exist and have cost attribute
    for route in initial_routes:
        edges = list(zip(route[:-1], route[1:]))
        for (i, j) in edges:
            if (i, j) not in G.edges():
                raise KeyError("Edge (%s,%s) in route %s missing in graph." %
                               (i, j, route))
            if "cost" not in G.edges[i, j]:
                raise KeyError("Edge (%s,%s) has no cost attribute." % (i, j))


def check_consistency(cspy: bool = None,
                      pickup_delivery: bool = None,
                      pricing_strategy: str = None,
                      G: DiGraph = None):
    """Raises errors if options are inconsistent with parameters."""

    # pickup delivery requires cspy=False
    if cspy and pickup_delivery:
        raise NotImplementedError("pickup_delivery option requires cspy=False.")
    # pickup delivery requires pricing_stragy="Exact"
    if pickup_delivery and pricing_strategy != "Exact":
        pricing_strategy = "Exact"
        logger.warning("Pricing_strategy changed to 'Exact'.")
    # pickup delivery expects at least one request
    if pickup_delivery:
        request = any("request" in G.nodes[v] for v in G.nodes())
        if not request:
            raise KeyError(
                "pickup_delivery option expects at least one request.")


def check_feasibility(load_capacity: list = None,
                      G: DiGraph = None,
                      duration: int = None):
    """Checks basic problem feasibility."""

    if load_capacity:
        for v in G.nodes():
            if G.nodes[v]["demand"] > max(load_capacity):
                raise ValueError(
                    "Demand %s at node %s larger than max capacity %s." %
                    (G.nodes[v]["demand"], v, max(load_capacity)))
    if duration:
        for v in G.nodes():
            if v not in ["Source", "Sink"]:
                round_trip_duration = (G.nodes[v]["service_time"] +
                                       G.edges["Source", v]["time"] +
                                       G.edges[v, "Sink"]["time"])
                if round_trip_duration > duration:
                    raise ValueError(
                        "Node %s not reachable: duration of path [Source,%s,Sink], %s, is larger than max duration %s."
                        % (v, v, round_trip_duration, duration))


def check_seed(seed):
    """Check whether given seed can be used to seed a numpy.random.RandomState
    :return: numpy.random.RandomState (seeded if seed given)
    """
    if seed is None:
        return RandomState()
    elif isinstance(seed, int):
        return RandomState(seed)
    elif isinstance(seed, RandomState):
        return seed
    else:
        raise TypeError("{} cannot be used to seed".format(seed))
