from networkx import DiGraph, negative_edge_cycle, shortest_path
import pulp
import logging

from vrpy.subproblem import _SubProblemBase

logger = logging.getLogger(__name__)


class _SubProblemLP(_SubProblemBase):
    """
    Solves the sub problem for the column generation procedure ; attemps
    to find routes with negative reduced cost.

    Inherits problem parameters from `SubproblemBase`
    """

    def __init__(self, *args, solver):
        super(_SubProblemLP, self).__init__(*args)
        # create problem
        self.prob = pulp.LpProblem("SubProblem", pulp.LpMinimize)
        # flow variables
        self.x = pulp.LpVariable.dicts("x", self.sub_G.edges(), cat=pulp.LpBinary)
        self.solver = solver

    # @profile
    def solve(self, time_limit, exact=True):
        if not self.run_subsolve:
            return self.routes, False
        if time_limit and time_limit <= 0:
            return self.routes, False

        self._formulate()
        if not exact:
            self._update_prob()
        # self.prob.writeLP("subprob.lp")
        self._solve(time_limit)

        logger.debug("Solving subproblem using LP")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective %s" % pulp.value(self.prob.objective))
        if (
            pulp.value(self.prob.objective) is not None
            and pulp.value(self.prob.objective) < -(10 ** -3)
        ) or (exact == False and pulp.LpStatus[self.prob.status] in ["Optimal", ""]):
            more_routes = True
            self._add_new_route()
        else:
            more_routes = False

        return self.routes, more_routes

    def _add_new_route(self):
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        self.total_cost = 0
        for (i, j) in self.sub_G.edges():
            if pulp.value(self.x[(i, j)]) > 0.5:
                edge_cost = self.sub_G.edges[i, j]["cost"][self.vehicle_type]
                self.total_cost += edge_cost
                new_route.add_edge(i, j, cost=edge_cost)
                if i != "Source":
                    self.routes_with_node[i].append(new_route)

        new_route.graph["cost"] = self.total_cost
        new_route.graph["vehicle_type"] = self.vehicle_type
        self.routes.append(new_route)

        logger.debug(
            "new route %s %s" % (route_id, shortest_path(new_route, "Source", "Sink"))
        )
        logger.debug("new route reduced cost %s" % pulp.value(self.prob.objective))
        logger.debug("new route cost = %s" % self.total_cost)
        # for (i, j) in new_route.edges():
        #    print(i, j, self.sub_G.edges[i, j])
        # routes_txt = open("routes.txt", "a")
        # routes_txt.write(str(shortest_path(new_route, "Source", "Sink")) + "\n")

    def _solve(self, time_limit):
        if self.solver == "cbc":
            self.prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
        elif self.solver == "cplex":
            self.prob.solve(pulp.CPLEX_CMD(msg=False, timeLimit=time_limit))
        elif self.solver == "gurobi":
            gurobi_options = []
            if time_limit is not None:
                gurobi_options.append(("TimeLimit", time_limit,))
            self.prob.solve(pulp.GUROBI(msg=False, options=gurobi_options))

    def _formulate(self):
        # minimize reduced cost
        self.prob += pulp.lpSum(
            [
                self.sub_G.edges[i, j]["weight"] * self.x[(i, j)]
                for (i, j) in self.sub_G.edges()
            ]
        )
        # flow balance
        for v in self.sub_G.nodes():
            if v not in ["Source", "Sink"]:
                in_flow = pulp.lpSum(
                    [self.x[(i, v)] for i in self.sub_G.predecessors(v)]
                )
                out_flow = pulp.lpSum(
                    [self.x[(v, j)] for j in self.sub_G.successors(v)]
                )
                self.prob += in_flow == out_flow, "flow_balance_%s" % v

        # Start at Source and end at Sink
        self.prob += (
            pulp.lpSum([self.x[("Source", v)] for v in self.sub_G.successors("Source")])
            == 1,
            "start_at_source",
        )
        self.prob += (
            pulp.lpSum([self.x[(u, "Sink")] for u in self.sub_G.predecessors("Sink")])
            == 1,
            "end_at_sink",
        )
        # Forbid route Source-Sink
        self.prob += (
            pulp.lpSum([self.x[(i, j)] for (i, j) in self.sub_G.edges()]) >= 2,
            "at_least_1_stop",
        )

        # Problem specific constraints
        if self.time_windows:
            self._add_time_windows()
        if self.num_stops:
            self._add_max_stops()
        if self.load_capacity:
            self._add_max_load()
        if self.duration:
            self._add_max_duration()
        self.elementarity = False
        if negative_edge_cycle(self.G):
            logger.debug("negative cycle found")
            self._add_elementarity()
            self.elementarity = True
        if self.pickup_delivery:
            self._add_pickup_delivery()
        if self.distribution_collection:
            self._add_distribution_collection()

    def _update_prob(self):
        """Reformulate to find a feasible solution with negative reduced cost."""

        # Update objective function (dummy)
        self.prob += 0
        # The solution must have a negative reduced cost
        self.prob += (
            pulp.lpSum(
                [
                    self.sub_G.edges[i, j]["weight"] * self.x[(i, j)]
                    for (i, j) in self.sub_G.edges()
                ]
            )
            <= -1
        )

    def _add_time_windows(self):
        # Big-M definition
        M = self.sub_G.nodes["Sink"]["upper"]
        # Add varibles
        self.t = pulp.LpVariable.dicts(
            "t", self.sub_G.nodes(), lowBound=0, cat=pulp.LpContinuous
        )
        # Add big-M constraints
        for (i, j) in self.sub_G.edges():
            self.prob += (
                self.t[i]
                + self.sub_G.nodes[i]["service_time"]
                + self.sub_G.edges[i, j]["time"]
                <= self.t[j] + M * (1 - self.x[(i, j)]),
                "time_window_%s_%s" % (i, j),
            )
        # Add node constraints
        for v in self.sub_G.nodes():
            self.prob += self.t[v] <= self.sub_G.nodes[v]["upper"], "node_%s_up" % v
            self.prob += self.t[v] >= self.sub_G.nodes[v]["lower"], "node_%s_low" % v

    def _add_max_stops(self):
        # Add max stop constraint
        # S stops => S+1 arcs
        self.prob += (
            pulp.lpSum([self.x[(i, j)] for (i, j) in self.sub_G.edges()])
            <= self.num_stops + 1,
            "max_{}".format(self.num_stops),
        )

    def _add_max_load(self):
        # Add maximum load constraints
        self.prob += (
            pulp.lpSum(
                [
                    self.sub_G.nodes[j]["demand"] * self.x[(i, j)]
                    for (i, j) in self.sub_G.edges()
                ]
            )
            <= self.load_capacity[self.vehicle_type],
            "max_load_{}".format(self.load_capacity[self.vehicle_type]),
        )

    def _add_max_duration(self):
        # Add maximum duration constraints
        self.prob += (
            pulp.lpSum(
                [
                    (
                        self.sub_G.edges[i, j]["time"]
                        + self.sub_G.nodes[i]["service_time"]
                    )
                    * self.x[(i, j)]
                    for (i, j) in self.sub_G.edges()
                ]
            )
            <= self.duration,
            "max_duration_{}".format(self.duration),
        )

    def _add_elementarity(self):
        """Ensures a node is visited at most once."""
        # Big-M definition
        M = len(self.sub_G.nodes())
        # Add rank varibles
        # y[v] = rank of node v in the path
        self.y = pulp.LpVariable.dicts(
            "y",
            self.sub_G.nodes(),
            lowBound=0,
            upBound=len(self.sub_G.nodes()),
            cat=pulp.LpInteger,
        )
        # Add big-M constraints
        for (i, j) in self.sub_G.edges():
            self.prob += (
                self.y[i] + 1 <= self.y[j] + M * (1 - self.x[(i, j)]),
                "elementary_%s_%s" % (i, j),
            )
        # Source is first, Sink is last (optional)
        self.prob += self.y["Source"] == 0, "Source_is_first"
        for v in self.sub_G.nodes():
            if v != "Sink":
                self.prob += self.y[v] <= self.y["Sink"], "Sink_after_%s" % v

    def _add_pickup_delivery(self):
        """
        Adds precedence and consistency constraints
        for pickup and delivery options.
        """
        if not self.elementarity:
            # rank variables are needed
            self._add_elementarity()
        for v in self.sub_G.nodes():
            if "request" in self.sub_G.nodes[v]:
                delivery_node = self.sub_G.nodes[v]["request"]
                # same vehicle for pickup and delivery node
                self.prob += (
                    pulp.lpSum([self.x[(v, u)] for u in self.sub_G.successors(v)])
                    == pulp.lpSum(
                        [
                            self.x[(delivery_node, u)]
                            for u in self.sub_G.successors(delivery_node)
                        ]
                    ),
                    "nodes_%s_%s_together" % (v, delivery_node),
                )

                # pickup before delivery
                self.prob += (
                    self.y[v] <= self.y[delivery_node],
                    "node_%s_before_%s" % (v, delivery_node),
                )

        # Variables to track the load on each node
        self.load = pulp.LpVariable.dicts(
            "load",
            self.sub_G.nodes(),
            lowBound=0,
            upBound=self.load_capacity[self.vehicle_type],
            cat=pulp.LpContinuous,
        )

        # Load definition
        M = self.load_capacity[self.vehicle_type]
        for (i, j) in self.sub_G.edges():
            self.prob += (
                self.load[i] + self.sub_G.nodes[j]["demand"]
                <= self.load[j] + M * (1 - self.x[(i, j)]),
                "inf_load_%s_%s" % (i, j),
            )
            self.prob += (
                self.load[i] + self.sub_G.nodes[j]["demand"]
                >= self.load[j] - M * (1 - self.x[(i, j)]),
                "sup_load_%s_%s" % (i, j),
            )
        # Empty load at depot
        self.prob += self.load["Source"] == 0, "source_load"
        self.prob += self.load["Sink"] == 0, "sink_load"

    def _add_distribution_collection(self):
        """
        The following formulation tracks the amount of load to be
        collected and delivered on each edge.
        https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118
        """
        # Variables to track the distribution load on each edge
        self.unload = pulp.LpVariable.dicts(
            "unload",
            self.sub_G.edges(),
            lowBound=0,
            upBound=self.load_capacity[self.vehicle_type],
            cat=pulp.LpContinuous,
        )
        # Variables to track the collection load on each edge
        self.load = pulp.LpVariable.dicts(
            "load",
            self.sub_G.edges(),
            lowBound=0,
            upBound=self.load_capacity[self.vehicle_type],
            cat=pulp.LpContinuous,
        )
        # unload definition (distribution)
        for v in self.sub_G.nodes():
            if v not in ["Source", "Sink"]:
                demand_v = self.sub_G.nodes[v]["demand"]
                distribution_load_from_v = pulp.lpSum(
                    [self.unload[(v, u)] for u in self.sub_G.successors(v)]
                )
                distribution_load_to_v = pulp.lpSum(
                    [self.unload[(u, v)] for u in self.sub_G.predecessors(v)]
                )
                is_used_v = pulp.lpSum(
                    [self.x[(u, v)] for u in self.sub_G.predecessors(v)]
                )
                self.prob += (
                    demand_v * is_used_v
                    == distribution_load_to_v - distribution_load_from_v,
                    "demand_%s" % v,
                )
        # load definition (collection)
        for v in self.sub_G.nodes():
            if v not in ["Source", "Sink"]:
                collect_v = self.sub_G.nodes[v]["collect"]
                collect_load_from_v = pulp.lpSum(
                    [self.load[(v, u)] for u in self.sub_G.successors(v)]
                )
                collect_load_to_v = pulp.lpSum(
                    [self.load[(u, v)] for u in self.sub_G.predecessors(v)]
                )
                is_used_v = pulp.lpSum(
                    [self.x[(u, v)] for u in self.sub_G.predecessors(v)]
                )
                self.prob += (
                    collect_v * is_used_v == collect_load_from_v - collect_load_to_v,
                    "collect_%s" % v,
                )
        # Max load per edge
        for (u, v) in self.sub_G.edges():
            self.prob += (
                self.load[(u, v)] + self.unload[(u, v)]
                <= self.load_capacity[self.vehicle_type] * self.x[(u, v)],
                "capacity_%s_%s" % (u, v),
            )
