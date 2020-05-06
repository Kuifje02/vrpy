from networkx import (
    compose_all,
    DiGraph,
    NetworkXException,
    add_path,
    has_path,
    shortest_simple_paths,
)
from itertools import islice


class SubProblemBase:
    """Base class for the subproblems.

    Args:
        G (DiGraph): Underlying network.
        duals (dict): Dual values of master problem.
        routes_with_node (dict): Keys : nodes ; Values : list of routes which contain the node.
        routes (list): Current routes/variables/columns.

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
        alpha (float, optional):
            Parameter in range (0,1) for pruning the graph.
            Defaults to None.
        beta (int, optional):
            Parameter > 1 for pruning the graph.
            Defaults to None.
        sub_G (DiGraph):
            Subgraph of G.
            The subproblem is based on sub_G.
        run_subsolve (boolean):
            True if the subproblem is solved.
    """

    def __init__(
        self,
        G,
        duals,
        routes_with_node,
        routes,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
        pickup_delivery=False,
        distribution_collection=False,
        alpha=None,
        beta=None,
    ):
        # Input attributes
        self.G = G
        self.duals = duals
        self.routes_with_node = routes_with_node
        self.routes = routes
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows
        self.pickup_delivery = pickup_delivery
        self.distribution_collection = distribution_collection
        self.run_subsolve = True

        # Add reduced cost to "weight" attribute
        self.add_reduced_cost_attribute()

        # Heuristically prune the graph
        if not self.pickup_delivery:  # this variant requires special treatment
            if beta:
                self.prune_subgraph_beta(beta)
            elif alpha:
                self.prune_subgraph_alpha(alpha)

    def add_reduced_cost_attribute(self):
        """Substracts the dual values to compute reduced cost on each edge."""
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"]
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]
        # Create a copy of G on which the subproblem is solved
        self.sub_G = self.G.copy()

    def prune_subgraph_alpha(self, alpha):
        """
        Removes edges based on criteria described here :
        https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118

        Edges for which [cost > alpha x largest dual value] are removed,
        where 0 < alpha < 1 is a parameter.
        """

        largest_dual = max([self.duals[v] for v in self.duals])
        for (u, v) in self.G.edges():
            if self.G.edges[u, v]["cost"] > alpha * largest_dual:
                self.sub_G.remove_edge(u, v)

        # If pruning the graph disconnects the source and the sink,
        # do not solve the subproblem.
        try:
            if not has_path(self.sub_G, "Source", "Sink"):
                self.run_subsolve = False
        except NetworkXException:
            self.run_subsolve = False

    def prune_subgraph_beta(self, beta):
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
        min_weight = min([self.G.edges[i, j]["weight"] for (i, j) in self.G.edges()])
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
        self.sub_G = self.sub_G.edge_subgraph(induced_graph.edges()).copy()
