from networkx import DiGraph
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

    def __init(self):
        # Attribute for the pulp.LpProblem
        self.prob = None
        # Attribute for the flow varibles
        self.x = None

    def solve(self):
        self.formulate()
        self.prob.solve()
        # if you have CPLEX
        # prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
        logger.debug("")
        logger.debug("Solving subproblem using LP")
        logger.debug("Status:", pulp.LpStatus[self.prob.status])
        logger.debug("Objective:", pulp.value(self.prob.objective))
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
        for (i, j) in self.G.edges():
            if pulp.value(self.x[(i, j)]) > 0.5:
                edge_cost = self.G.edges[i, j]["cost"]
                self.total_cost += edge_cost
                new_route.add_edge(i, j, cost=edge_cost)
        new_route.graph["cost"] = self.total_cost
        self.routes.append(new_route)
        logger.debug("new route", route_id, new_route.edges())
        logger.debug("new route cost =", self.total_cost)

    def formulate(self):
        # create problem
        self.prob = pulp.LpProblem("SubProblem", pulp.LpMinimize)
        # flow variables
        self.x = pulp.LpVariable.dicts("x", self.G.edges(), cat=pulp.LpBinary)
        # minimize reduced cost
        edge_cost = pulp.lpSum(
            [self.G.edges[i, j]["cost"] * self.x[(i, j)] for (i, j) in self.G.edges()]
        )
        dual_cost = pulp.lpSum(
            [
                self.x[(v, j)] * self.duals[v]
                for v in self.G.nodes()
                if v not in ["Source"]
                for j in self.G.successors(v)
            ]
        )
        self.prob += edge_cost - dual_cost
        # flow balance
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                in_flow = pulp.lpSum([self.x[(i, v)] for i in self.G.predecessors(v)])
                out_flow = pulp.lpSum([self.x[(v, j)] for j in self.G.successors(v)])
                self.prob += in_flow == out_flow, "flow_balance_%s" % v
        # Problem specific constraints
        if self.time_windows:
            self.add_time_windows()
        if self.num_stops:
            self.add_max_stops()
        if self.load_capacity:
            self.add_max_load()
        if self.duration:
            self.add_max_duration()

    def add_time_windows(self):
        # Big-M definition
        M = 1e10
        # Add varibles
        t = pulp.LpVariable.dicts(
            "t", self.G.nodes(), lowBound=0, cat=pulp.LpContinuous
        )
        # Add big-M constraints
        for (i, j) in self.G.edges():
            self.prob += (
                t[i] + self.G.edges[i, j]["time"] <= t[j] + M * (1 - self.x[(i, j)]),
                "time_window_%s_%s" % (i, j),
            )
        # Add node constraints
        for v in self.G.nodes():
            self.prob += t[v] <= self.G.nodes[v]["upper"], "node_%s_up" % v
            self.prob += t[v] >= self.G.nodes[v]["lower"], "node_%s_low" % v

    def add_max_stops(self):
        # Add max stop constraint
        # S stops => S+1 arcs
        self.prob += (
            pulp.lpSum([self.x[(i, j)] for (i, j) in self.G.edges()])
            <= self.num_stops + 1,
            "max_{}".format(self.num_stops),
        )

    def add_max_load(self):
        # Add maximum load constraints
        self.prob += (
            pulp.lpSum(
                [
                    self.G.nodes[j]["demand"] * self.x[(i, j)]
                    for (i, j) in self.G.edges()
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
                    self.G.edges[i, j]["time"] * self.x[(i, j)]
                    for (i, j) in self.G.edges()
                ]
            )
            <= self.duration,
            "max_duration_{}".format(self.duration),
        )
