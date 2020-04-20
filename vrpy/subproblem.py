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

        # Prune the graph
        infeasible_arcs = []
        # remove infeasible arcs (capacities)
        if load_capacity:
            for (i, j) in G.edges():
                if G.nodes[i]["demand"] + G.nodes[j]["demand"] > load_capacity:
                    infeasible_arcs.append((i, j))

        # remove infeasible arcs (time windows)
        if time_windows:
            for (i, j) in G.edges():
                travel_time = G.edges[i, j]["time"]
                service_time = 0  # for now
                tail_inf_time_window = G.nodes[i]["lower"]
                head_sup_time_window = G.nodes[j]["upper"]
                if (
                    tail_inf_time_window + travel_time + service_time
                    > head_sup_time_window
                ):
                    infeasible_arcs.append((i, j))
        G.remove_edges_from(infeasible_arcs)
