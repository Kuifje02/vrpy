import logging

logger = logging.getLogger(__name__)


class _Greedy:
    """
    Greedy algorithm. Iteratively adds closest feasible node to current path.

    Args:
        G (DiGraph): Graph on which algorithm is run.
        load_capacity (int, optional) : Maximum load per route. Defaults to None.
        num_stops (int, optional) : Maximum stops per route. Defaults to None.
    """

    def __init__(self, G, load_capacity=None, num_stops=None, duration=None):
        self.G = G.copy()
        self._format_cost()
        self._best_routes = []
        self._unprocessed_nodes = [
            v for v in self.G.nodes() if v not in ["Source", "Sink"]
        ]

        if isinstance(load_capacity, list):
            # capacity of vehicle type 1 is used!
            self.load_capacity = load_capacity[0]
        else:
            self.load_capacity = load_capacity
        self.num_stops = num_stops
        self.duration = duration

        self._best_value = 0

    @property
    def best_value(self):
        return self._best_value

    @property
    def best_routes(self):
        return self._best_routes

    def run(self):
        """The forward search is run."""
        while self._unprocessed_nodes != []:
            self._load = 0
            self._stops = 0
            self._time = 0
            self._run_forward()
            self._update_routes()
            if self._current_path == ["Source", "Sink"]:
                break

    def _run_forward(self):
        """
        A path starting from Source is greedily extended
        until Sink is reached.
        The procedure aborts if path becomes infeasible.
        """
        self._current_path = ["Source"]
        while True:
            self._get_next_node()
            self._update()
            if self._new_node == "Sink":
                break

    def _get_next_node(self):
        self._last_node = self._current_path[-1]
        out_going_costs = {}
        # Store the successors cost that meet constraints
        for v in self.G.successors(self._last_node):
            if self._constraints_met(v) and v in self._unprocessed_nodes:
                out_going_costs[v] = self.G.edges[self._last_node, v]["cost"]
        if out_going_costs == {}:
            logger.debug("path cannot be extended")
            self._new_node = "Sink"
        else:
            # Select best successor
            self._new_node = sorted(out_going_costs, key=out_going_costs.get)[0]

    def _constraints_met(self, v):
        """Checks if constraints are respected."""
        if v in self._current_path or self._check_source_sink(v):
            return False
        elif self.load_capacity and not self._check_capacity(v):
            return False
        elif self.duration and not self._check_duration(v):
            return False
        else:
            return True

    def _update(self):
        """Updates path, path load, unprocessed nodes."""
        self._load += self.G.nodes[self._new_node]["demand"]
        last_node = self._current_path[-1]
        self._current_path.append(self._new_node)
        if self._new_node not in ["Source", "Sink"]:
            self._unprocessed_nodes.remove(self._new_node)
        self._stops += 1
        self._best_value += self.G.edges[last_node, self._new_node]["cost"]
        self._time += (
            self.G.edges[last_node, self._new_node]["time"]
            + self.G.nodes[self._new_node]["service_time"]
        )
        if self._stops == self.num_stops and self._new_node != "Sink":
            # End path
            self._current_path.append("Sink")
            if self._new_node in self.G.predecessors("Sink"):
                self._best_value += self.G.edges[self._new_node, "Sink"]["cost"]
                self._new_node = "Sink"
            else:
                self._best_value += 1e10
                self._current_path = None

    def _update_routes(self):
        """Stores best routes as list of nodes."""
        if self._current_path:
            self._best_routes.append(self._current_path)

    def _check_source_sink(self, v):
        """Checks if edge Source Sink."""
        return self._last_node == "Source" and v == "Sink"

    def _check_capacity(self, v):
        """Checks capacity constraint."""
        return self._load + self.G.nodes[v]["demand"] <= self.load_capacity

    def _check_duration(self, v):
        """Checks duration constraint."""
        u = self._current_path[-1]
        return_time = self.G.edges[v, "Sink"]["time"] if v != "Sink" else 0
        return (
            self._time
            + self.G.nodes[v]["service_time"]
            + self.G.edges[u, v]["time"]
            + return_time
            <= self.duration
        )

    def _format_cost(self):
        """If list of costs is given, first item of list is considered."""
        for (i, j) in self.G.edges():
            if isinstance(self.G.edges[i, j]["cost"], list):
                self.G.edges[i, j]["cost"] = self.G.edges[i, j]["cost"][0]
