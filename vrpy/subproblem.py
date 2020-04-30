from networkx import NetworkXException, has_path


class SubProblemBase:
    """Base class for the subproblems.

    Args:
        G (DiGraph): Underlying network.
        duals (dict): Dual values of master problem.
        routes_with_node (dict): Keys : nodes ; Values : list of routes which contain the node.
        routes (list): Current routes/variables/columns.
        alpha (float): Parameter in range (0,1) for pruning the graphe.

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
        undirected (bool, optional):
            True if underlying network is undirected.
            Defaults to True.
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
        undirected=True,
        alpha=1,
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
        self.undirected = undirected

        # Add reduced cost to "weight" attribute
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"]
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]

        # Create a copy of G on which the subproblem is solved
        self.sub_G = self.G.copy()
        self.run_subsolve = True

        # Heuristically prune the graph if alpha < 1
        if alpha < 1:
            self.prune_subgraph(alpha)

    def prune_subgraph(self, alpha):
        """
        Removes edges based on criteria described here :
        https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118

        Edges for which [cost > alpha x largest dual value] are removed,
        where 0 < alpha < 1.
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

        """
        for v in self.G.nodes():
            if v not in ["Source", "Sink"] and self.duals[v] <= 0:
                self.sub_G.remove_node(v)
        """
