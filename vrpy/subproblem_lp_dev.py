from networkx import DiGraph, negative_edge_cycle, shortest_path
import pulp
from subproblem import SubProblemBase
import logging

logger = logging.getLogger(__name__)


class SubProblemLP(SubProblemBase):
    """
    Solves the sub problem for the column generation procedure ; attemps
    to find routes with negative reduced cost.

    Inherits problem parameters from `SubproblemBase`
    """

    def __init__(self, *args):
        super(SubProblemLP, self).__init__(*args)
        # create problem
        self.prob = pulp.LpProblem("SubProblem", pulp.LpMinimize)
        # flow variables
        self.x = pulp.LpVariable.dicts("x", self.H.edges(), cat=pulp.LpBinary)

    # @profile
    def solve(self):
        self.formulate()
        # self.prob.writeLP("prob.lp")
        self.prob.solve()
        # if you have CPLEX
        # self.prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
        logger.debug("")
        logger.debug("Solving subproblem using LP")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective %s" % pulp.value(self.prob.objective))
        if pulp.value(self.prob.objective) < -(10 ** -5):
            more_routes = True
            self.add_new_route()
            return self.routes, more_routes
        else:
            more_routes = False
            return self.routes, more_routes

    def add_new_route(self):
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        self.total_cost = 0
        for (i, j) in self.H.edges():
            if pulp.value(self.x[(i, j)]) > 0.5:
                edge_cost = self.H.edges[i, j]["cost"]
                self.total_cost += edge_cost
                new_route.add_edge(i, j, cost=edge_cost)
                if self.time_windows:
                    new_route.nodes[i]["time"] = pulp.value(self.t[i])
                    # new_route.nodes["Sink"]["time"] = pulp.value(self.t["Sink"])
        new_route.graph["cost"] = self.total_cost
        self.routes.append(new_route)
        logger.debug("new route %s %s" % (route_id, new_route.edges()))
        # for (i, j) in new_route.edges():
        #    print(i, j, self.H.edges[i, j])
        logger.debug("new route cost = %s" % self.total_cost)
        # routes_txt = open("routes.txt", "a")
        # routes_txt.write(str(shortest_path(new_route, "Source", "Sink")) + "\n")

    def formulate(self):
        # minimize reduced cost
        self.prob += pulp.lpSum(
            [self.H.edges[i, j]["weight"] * self.x[(i, j)] for (i, j) in self.H.edges()]
        )
        # flow balance
        for v in self.H.nodes():
            if v not in ["Source", "Sink"]:
                in_flow = pulp.lpSum([self.x[(i, v)] for i in self.H.predecessors(v)])
                out_flow = pulp.lpSum([self.x[(v, j)] for j in self.H.successors(v)])
                self.prob += in_flow == out_flow, "flow_balance_%s" % v

        # Start at Source and end at Sink
        self.prob += (
            pulp.lpSum([self.x[("Source", v)] for v in self.H.successors("Source")])
            == 1,
            "start_at_source",
        )
        self.prob += (
            pulp.lpSum([self.x[(u, "Sink")] for u in self.H.predecessors("Sink")]) == 1,
            "end_at_sink",
        )
        # Forbid route Source-Sink
        self.prob += (
            pulp.lpSum([self.x[(i, j)] for (i, j) in self.H.edges()]) >= 2,
            "at_least_1_stop",
        )

        # Problem specific constraints
        if self.time_windows:
            self.add_time_windows()
        if self.num_stops:
            self.add_max_stops()
        if self.load_capacity:
            self.add_max_load()
        if self.duration:
            self.add_max_duration()
        self.elementarity = False
        if negative_edge_cycle(self.G):
            logger.debug("negative cycle found")
            self.add_elementarity()
            self.elementarity = True

        # Break some symmetry
        # if self.undirected and not self.time_windows:
        #    self.break_symmetry()

        if self.pickup_delivery:
            self.add_pickup_delivery()

    def add_time_windows(self):
        # Big-M definition
        M = self.H.nodes["Sink"]["upper"]
        # Add varibles
        self.t = pulp.LpVariable.dicts(
            "t", self.H.nodes(), lowBound=0, cat=pulp.LpContinuous
        )
        # Add big-M constraints
        for (i, j) in self.H.edges():
            self.prob += (
                self.t[i] + self.H.nodes[i]["service_time"] + self.H.edges[i, j]["time"]
                <= self.t[j] + M * (1 - self.x[(i, j)]),
                "time_window_%s_%s" % (i, j),
            )
        # Add node constraints
        for v in self.H.nodes():
            self.prob += self.t[v] <= self.H.nodes[v]["upper"], "node_%s_up" % v
            self.prob += self.t[v] >= self.H.nodes[v]["lower"], "node_%s_low" % v

    def add_max_stops(self):
        # Add max stop constraint
        # S stops => S+1 arcs
        self.prob += (
            pulp.lpSum([self.x[(i, j)] for (i, j) in self.H.edges()])
            <= self.num_stops + 1,
            "max_{}".format(self.num_stops),
        )

    def add_max_load(self):
        # Add maximum load constraints
        self.prob += (
            pulp.lpSum(
                [
                    self.H.nodes[j]["demand"] * self.x[(i, j)]
                    for (i, j) in self.H.edges()
                ]
            )
            <= self.load_capacity,
            "max_load_".format(self.load_capacity),
        )

    def add_max_duration(self):
        # Add maximum duration constraints
        self.prob += (
            pulp.lpSum(
                [
                    (self.H.edges[i, j]["time"] + self.H.nodes[i]["service_time"])
                    * self.x[(i, j)]
                    for (i, j) in self.H.edges()
                ]
            )
            <= self.duration,
            "max_duration_{}".format(self.duration),
        )

    def add_elementarity(self):
        """Ensures a node is visited at most once."""
        # Big-M definition
        M = len(self.H.nodes())
        # Add rank varibles
        # y[v] = rank of node v in the path
        self.y = pulp.LpVariable.dicts(
            "y",
            self.H.nodes(),
            lowBound=0,
            upBound=len(self.H.nodes()),
            cat=pulp.LpInteger,
        )
        # Add big-M constraints
        for (i, j) in self.H.edges():
            self.prob += (
                self.y[i] + 1 <= self.y[j] + M * (1 - self.x[(i, j)]),
                "elementary_%s_%s" % (i, j),
            )
        # Source is first, Sink is last (optional)
        self.prob += self.y["Source"] == 0, "Source_is_first"
        for v in self.H.nodes():
            if v != "Sink":
                self.prob += self.y[v] <= self.y["Sink"], "Sink_after_%s" % v

    def break_symmetry(self):
        """If the graph is undirected, divide the number of possible paths by 2."""
        # index of first node < index of last node
        self.prob += (
            pulp.lpSum(
                [
                    self.H.nodes[v]["id"] * self.x[("Source", v)]
                    for v in self.H.successors("Source")
                ]
            )
            <= pulp.lpSum(
                [
                    self.H.nodes[v]["id"] * self.x[(v, "Sink")]
                    for v in self.H.predecessors("Sink")
                ]
            ),
            "break_symmetry",
        )

    def add_pickup_delivery(self):
        """
        Adds precedence and consistency constraints 
        for pickup and delivery options.
        """
        for v in self.H.nodes():
            if "request" in self.H.nodes[v]:
                delivery_node = self.H.nodes[v]["request"]

                # same vehicle for pickup and delivery node
                self.prob += (
                    pulp.lpSum([self.x[(v, u)] for u in self.H.successors(v)])
                    == pulp.lpSum(
                        [
                            self.x[(delivery_node, u)]
                            for u in self.H.successors(delivery_node)
                        ]
                    ),
                    "nodes_%s_%s_together" % (v, delivery_node),
                )

                # pickup before delivery
                if not self.add_elementarity:
                    self.add_elementarity()
                self.prob += (
                    self.y[v] <= self.y[delivery_node],
                    "node_%s_before_%s" % (v, delivery_node),
                )
