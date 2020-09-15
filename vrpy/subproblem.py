import logging
from itertools import islice

from networkx import (
    compose_all,
    DiGraph,
    NetworkXException,
    add_path,
    has_path,
    shortest_simple_paths,
)

logger = logging.getLogger(__name__)


class _SubProblemBase:
    """
    Base class for the subproblems.

    Args:
        G (DiGraph): Underlying network.
        duals (dict): Dual values of master problem.
        routes_with_node (dict): Keys : nodes ; Values : list of routes which contain the node.
        routes (list): Current routes/variables/columns.
        vehicle_type (int): Current vehicle type.
        route (DiGraph):
            Current route.
            Is not None if pricing problem is route dependent (e.g, when minimizing global span).

    Attributes:
        num_stops (int, optional):
            Maximum number of stops.
            If not provided, constraint not enforced.
        load_capacity (int, optional):
            Maximum capacity.
            If not provided, constraint not enforced.
        duration (int, optional):
            Maximum duration.
            If not provided, constraint not enforced.
        time_windows (bool, optional):
            True if time windows activated.
            Defaluts to False.
        pickup_delivery (bool, optional):
            True if pickup and delivery constraints.
            Defaults to False.
        distribution_collection (bool, optional):
            True if distribution and collection are simultaneously enforced.
            Defaults to False.
        sub_G (DiGraph):
            Subgraph of G.
            The subproblem is based on sub_G.
        run_subsolve (boolean):
            True if the subproblem is solved.
        pricing_strategy (string):
            Strategy used for solving subproblem.
            Either "Exact", "BestEdges1", "BestEdges2", "BestPaths".
            Defaults to "BestEdges1".
        pricing_parameter (float):
            Parameter used depending on pricing_strategy.
            Defaults to None.
    """

    def __init__(
        self,
        G,
        duals,
        routes_with_node,
        routes,
        vehicle_type,
        route=None,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
        pickup_delivery=False,
        distribution_collection=False,
        pricing_strategy="Exact",
        pricing_parameter=None,
    ):
        # Input attributes
        self.G = G
        self.duals = duals
        self.routes_with_node = routes_with_node
        self.routes = routes
        self.vehicle_type = vehicle_type
        self.route = route
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows
        self.pickup_delivery = pickup_delivery
        self.distribution_collection = distribution_collection
        self.run_subsolve = True

        # Add reduced cost to "weight" attribute
        self.add_reduced_cost_attribute()
        # print(self.duals)
        # for (i, j) in self.G.edges():
        #    print(i, j, self.G.edges[i, j])

        # Define the graph on which the sub problem is solved according to the pricing strategy
        if pricing_strategy == "BestEdges1":
            # The graph is pruned
            self.remove_edges_1(pricing_parameter)
        elif pricing_strategy == "BestEdges2":
            # The graph is pruned
            self.remove_edges_2(pricing_parameter)
        elif pricing_strategy == "BestPaths":
            # The graph is pruned
            self.remove_edges_3(pricing_parameter)

        elif pricing_strategy == "Exact":
            # The graph remains as is
            self.sub_G = self.G
        logger.debug("Pricing strategy %s, %s" % (pricing_strategy, pricing_parameter))

    def add_reduced_cost_attribute(self):
        """Substracts the dual values to compute reduced cost on each edge."""
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"][self.vehicle_type]
            if self.route:
                edge[2]["weight"] *= -self.duals[
                    "makespan_%s" % self.route.graph["name"]
                ]
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]
        if "upper_bound_vehicles" in self.duals:
            for v in self.G.successors("Source"):
                self.G.edges["Source", v]["weight"] -= self.duals[
                    "upper_bound_vehicles"
                ][self.vehicle_type]

    def discard_nodes(self):
        """Removes nodes with marginal cost = 0."""
        for v in self.duals:
            if v != "upper_bound_vehicles" and self.duals[v] == 0:
                self.sub_G.remove_node(v)
                print("removed node", v)

    def remove_edges_1(self, alpha):
        """
        Removes edges based on criteria described here :
        https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118

        Edges for which [cost > alpha x largest dual value] are removed,
        where 0 < alpha < 1 is a parameter.
        """
        self.sub_G = self.G.copy()
        largest_dual = max(
            self.duals[v] for v in self.duals if v != "upper_bound_vehicles"
        )

        for (u, v) in self.G.edges():
            if self.G.edges[u, v]["cost"][self.vehicle_type] > alpha * largest_dual:
                self.sub_G.remove_edge(u, v)
        # If pruning the graph disconnects the source and the sink,
        # do not solve the subproblem.
        try:
            if not has_path(self.sub_G, "Source", "Sink"):
                self.run_subsolve = False
        except NetworkXException:
            self.run_subsolve = False

    def remove_edges_2(self, ratio):
        """
        Removes edges based on criteria described here :
        https://www.sciencedirect.com/science/article/abs/pii/S0377221717306045

        Edges are sorted by non decreasing reduced cost, and only
        the K|E| ones with lowest reduced cost are kept, where K is a parameter (ratio).
        """
        self.sub_G = self.G.copy()
        # Sort the edges by non decreasing reduced cost
        reduced_cost = {}
        for (u, v) in self.G.edges():
            if u != "Source" and v != "Sink":
                reduced_cost[(u, v)] = self.G.edges[u, v]["weight"]
        sorted_edges = sorted(reduced_cost, key=reduced_cost.get)
        # Keep the best ones
        limit = int(ratio * len(sorted_edges))
        self.sub_G.remove_edges_from(sorted_edges[limit:])
        # If pruning the graph disconnects the source and the sink,
        # do not solve the subproblem.
        try:
            if not has_path(self.sub_G, "Source", "Sink"):
                self.run_subsolve = False
        except NetworkXException:
            self.run_subsolve = False

    def remove_edges_3(self, beta):
        """
        Heuristic pruning:
        1. Normalize weights in interval [-1,1]
        2. Set all negative weights to 0
        3. Compute beta shortest paths (beta is a paramater)
           https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html
        4. Remove all edges that do not belong to these paths
        """
        # Normalize weights
        max_weight = max([self.G.edges[i, j]["weight"] for (i, j) in self.G.edges()])
        min_weight = min(self.G.edges[i, j]["weight"] for (i, j) in self.G.edges())
        for edge in self.G.edges(data=True):
            edge[2]["pos_weight"] = (
                -max_weight - min_weight + 2 * edge[2]["weight"]
            ) / (max_weight - min_weight)
            edge[2]["pos_weight"] = max(0, edge[2]["pos_weight"])
        # Compute beta shortest paths
        best_paths = list(
            islice(
                shortest_simple_paths(self.G, "Source", "Sink", weight="pos_weight"),
                beta,
            )
        )
        # Store these paths as a list of DiGraphs
        best_paths_list = []
        for path in best_paths:
            H = DiGraph()
            add_path(H, path)
            best_paths_list.append(H)
        # Merge the paths into one graph
        induced_graph = compose_all(best_paths_list)
        # Create subgraph induced by the edges of this graph
        self.sub_G = self.G.edge_subgraph(induced_graph.edges()).copy()
