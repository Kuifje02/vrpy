class SubProblemBase:
    """Base class for the subproblems.

    Args:
        G (DiGraph): Underlying network
        duals (dict): Dual values of master problem
        routes (list): Current routes/variables/columns

    Attributes:
        num_stops (int):
            Maximum number of stops. Optional.
            If not provided, constraint not enforced.
        load_capacity (int):
            Maximum capacity. Optional.
            If not provided, constraint not enforced.
        duration (int):
            Maximum duration. Optional.
            If not provided, constraint not enforced.
        time_windows (bool):
            True if time windows activated
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
    ):
        # Input attributes
        self.G = G
        self.duals = duals
        self.routes = routes
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows

        # Add reduced cost to "weight" attribute
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"]
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]

