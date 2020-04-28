class SubProblemBase:
    """Base class for the subproblems.

    Args:
        G (DiGraph): Underlying network
        duals (dict): Dual values of master problem
        routes (list): Current routes/variables/columns

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
    """

    def __init__(
        self,
        G,
        duals,
        routes,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
        pickup_delivery=False,
        distribution_collection=False,
        undirected=True,
    ):
        # Input attributes
        self.G = G
        self.duals = duals
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
