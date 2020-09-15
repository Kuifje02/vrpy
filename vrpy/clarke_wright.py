from networkx import DiGraph, add_path, shortest_path


class _ClarkeWright:
    """
    Clarke & Wrights savings algorithm.

    Args:
        G (DiGraph): Graph on which algorithm is run.
        load_capacity (int, optional) : Maximum load per route. Defaults to None.
        duration (int, optional) : Maximum duration per route. Defaults to None.
        num_stops (int, optional) : Maximum number of stops per route. Defaults to None.
    """

    def __init__(
        self,
        G,
        load_capacity=None,
        duration=None,
        num_stops=None,
        alpha=1,
        beta=0,
        gamma=0,
    ):
        self.G = G.copy()
        self._format_cost()
        self._savings = {}
        self._ordered_edges = []
        self._route = {}
        self._best_routes = []
        self._processed_nodes = []

        self.alpha = alpha
        # FOR MORE SOPHISTICATED VERSIONS OF CLARKE WRIGHT:
        # self.beta = beta
        # self.gamma = gamma
        # self._average_demand = sum(
        #    [
        #        self.G.nodes[v]["demand"]
        #        for v in self.G.nodes()
        #        if self.G.nodes[v]["demand"] > 0
        #    ]
        # ) / len([v for v in self.G.nodes() if self.G.nodes[v]["demand"] > 0])

        if isinstance(load_capacity, list):
            self.load_capacity = load_capacity[0]
        else:
            self.load_capacity = load_capacity
        self.duration = duration
        self.num_stops = num_stops

    def run(self):
        """Runs Clark & Wrights savings algorithm."""
        self._initialize_routes()
        self._get_savings()
        for (i, j) in self._ordered_edges:
            self._process_edge(i, j)
        self._update_routes()

    def _initialize_routes(self):
        """Initialization with round trips (Source - node - Sink)."""
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                # Create round trip
                round_trip_cost = (
                    self.G.edges["Source", v]["cost"] + self.G.edges[v, "Sink"]["cost"]
                )
                route = DiGraph(cost=round_trip_cost)
                add_path(route, ["Source", v, "Sink"])
                self._route[v] = route
                # Initialize route attributes
                if self.load_capacity:
                    route.graph["load"] = self.G.nodes[v]["demand"]
                if self.duration:
                    route.graph["time"] = (
                        self.G.nodes[v]["service_time"]
                        + self.G.edges["Source", v]["time"]
                        + self.G.edges[v, "Sink"]["time"]
                    )

    def _update_routes(self):
        """Stores best routes as list of nodes."""
        self._best_value = 0
        for route in list(set(self._route.values())):
            self._best_value += route.graph["cost"]
            self._best_routes.append(shortest_path(route, "Source", "Sink"))

    def _get_savings(self):
        """Computes Clark & Wright savings and orders edges by non increasing savings."""
        for (i, j) in self.G.edges():
            if i != "Source" and j != "Sink":
                self._savings[(i, j)] = (
                    self.G.edges[i, "Sink"]["cost"]
                    + self.G.edges["Source", j]["cost"]
                    - self.alpha * self.G.edges[i, j]["cost"]
                    # FOR MORE SOPHISTICATED VERSIONS OF CLARKE WRIGHT:
                    # + self.beta
                    # * abs(
                    #    self.G.edges["Source", i]["cost"]
                    #    - self.G.edges[j, "Sink"]["cost"]
                    # )
                    # + self.gamma
                    # * (self.G.nodes[i]["demand"] + self.G.nodes[j]["demand"])
                    # / self._average_demand
                )
        self._ordered_edges = sorted(self._savings, key=self._savings.get, reverse=True)

    def _merge_route(self, existing_node, new_node, depot):
        """
        Merges new_node in existing_node's route.
        Two possibilities:
            1. If existing_node is a predecessor of Sink, new_node is inserted
               between existing_node and Sink;
            2. If existing_node is a successor of Source, new_node is inserted
               between Source and and existing_node.
        """
        route = self._route[existing_node]
        # Insert new_node between existing_node and Sink
        if depot == "Sink":
            add_path(route, [existing_node, new_node, "Sink"])
            route.remove_edge(existing_node, "Sink")
            # Update route cost
            self._route[existing_node].graph["cost"] += (
                self.G.edges[existing_node, new_node]["cost"]
                + self.G.edges[new_node, "Sink"]["cost"]
                - self.G.edges[existing_node, "Sink"]["cost"]
            )

        # Insert new_node between Source and existing_node
        if depot == "Source":
            add_path(route, ["Source", new_node, existing_node])
            route.remove_edge("Source", existing_node)
            # Update route cost
            self._route[existing_node].graph["cost"] += (
                self.G.edges[new_node, existing_node]["cost"]
                + self.G.edges["Source", new_node]["cost"]
                - self.G.edges["Source", existing_node]["cost"]
            )

        # Update route load
        if self.load_capacity:
            self._route[existing_node].graph["load"] += self.G.nodes[new_node]["demand"]
        # Update route duration
        if self.duration:
            self._route[existing_node].graph["time"] += (
                self.G.edges[existing_node, new_node]["time"]
                + self.G.edges[new_node, "Sink"]["time"]
                + self.G.nodes[new_node]["service_time"]
                - self.G.edges[existing_node, "Sink"]["time"]
            )
        # Update processed vertices
        self._processed_nodes.append(new_node)
        if existing_node not in self._processed_nodes:
            self._processed_nodes.append(existing_node)

        self._route[new_node] = route
        return route

    def _constraints_met(self, existing_node, new_node):
        """Tests if new_node can be merged in route without violating constraints."""
        route = self._route[existing_node]
        # test if new_node already in route
        if new_node in route.nodes():
            return False
        # test capacity constraints
        if self.load_capacity:
            if (
                route.graph["load"] + self.G.nodes[new_node]["demand"]
                > self.load_capacity
            ):
                return False
        # test duration constraints
        if self.duration:
            # this code assumes the times to go from the Source and to the Sink are equal
            if (
                route.graph["time"]
                + self.G.edges[existing_node, new_node]["time"]
                + self.G.edges[new_node, "Sink"]["time"]
                + self.G.nodes[new_node]["service_time"]
                - self.G.edges[existing_node, "Sink"]["time"]
                > self.duration
            ):
                return False
        # test stop constraints
        if self.num_stops:
            # Source and Sink don't count (hence -2)
            if len(route.nodes()) - 2 + 1 > self.num_stops:
                return False
        return True

    def _process_edge(self, i, j):
        """
        Attemps to merge nodes i and j together.
        Merge is possible if :
            1. vertices have not been merged already;
            2. route constraints are met;
            3. either:
               a) node i is adjacent to the Source (j is inserted in route[i]);
               b) or node j is adjacent to the Sink (i is inserted in route[j]).
        """
        merged = False
        if (
            j not in self._processed_nodes  # 1
            and self._constraints_met(i, j)  # 2
            and i in self._route[i].predecessors("Sink")  # 3b
        ):
            self._merge_route(i, j, "Sink")
            merged = True

        if (
            not merged
            and j in self.G.predecessors(i)
            and i not in self._processed_nodes  # 1
            and self._constraints_met(j, i)  # 2
            and j in self._route[j].successors("Source")  # 3a
        ):
            self._merge_route(j, i, "Source")

    def _format_cost(self):
        """If list of costs is given, first item of list is considered."""
        for (i, j) in self.G.edges():
            if isinstance(self.G.edges[i, j]["cost"], list):
                self.G.edges[i, j]["cost"] = self.G.edges[i, j]["cost"][0]

    @property
    def best_value(self):
        return self._best_value

    @property
    def best_routes(self):
        return self._best_routes


class _RoundTrip:
    """
    Computes simple round trips from the depot to each node (Source-node-Sink).

    Args:
        G (DiGraph): Graph on which round trips are computed.
    """

    def __init__(self, G):
        self.G = G
        self.round_trips = []

    def run(self):
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                self.round_trips.append(["Source", v, "Sink"])
