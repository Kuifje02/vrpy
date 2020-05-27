import pulp
import logging
from networkx import shortest_path
from vrpy.masterproblem import MasterProblemBase

logger = logging.getLogger(__name__)


class MasterSolvePulp(MasterProblemBase):
    """
    Solves the master problem for the column generation procedure.

    Inherits problem parameters from MasterProblemBase
    """

    def solve(self, solver, time_limit):
        self.formulate()
        # self.prob.writeLP("masterprob.lp")
        if solver == "cbc":
            self.prob.solve(pulp.PULP_CBC_CMD(maxSeconds=time_limit))
        elif solver == "cplex":
            self.prob.solve(pulp.solvers.CPLEX_CMD(timelimit=time_limit))
        elif solver == "gurobi":
            gurobi_options = [("TimeLimit", time_limit)]
            self.prob.solve(pulp.solvers.GUROBI_CMD(options=gurobi_options))
        logger.debug("master problem")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective: %s" % pulp.value(self.prob.objective))

        if pulp.LpStatus[self.prob.status] != "Optimal":
            raise Exception("problem " + str(pulp.LpStatus[self.prob.status]))
        if self.relax:
            for r in self.routes:
                if pulp.value(self.y[r.graph["name"]]) > 0.5:
                    logger.debug("route %s selected" % r.graph["name"])
            duals = self.get_duals()
            logger.debug("duals : %s" % duals)
            return duals, pulp.value(self.prob.objective)

        else:
            best_routes = []
            for r in self.routes:
                val = pulp.value(self.y[r.graph["name"]])
                if val is not None and val > 0:
                    logger.debug(
                        "%s cost %s load %s"
                        % (
                            shortest_path(r, "Source", "Sink"),
                            r.graph["cost"],
                            sum([self.G.nodes[v]["demand"] for v in r.nodes()]),
                        )
                    )
                    best_routes.append(r)
            if self.drop_penalty:
                self.dropped_nodes = [
                    v for v in self.drop if pulp.value(self.drop[v]) > 0.5
                ]
            total_cost = pulp.value(self.prob.objective)
            if not self.relax and self.drop_penalty and len(self.dropped_nodes) > 0:
                logger.info("dropped nodes : %s" % self.dropped_nodes)
            logger.info("total cost = %s" % total_cost)
            if not total_cost:
                total_cost = 0
            return total_cost, best_routes

    def formulate(self):
        """
        Set covering formulation.
        Variables are continuous when relaxed, otherwise binary.
        """
        # create problem
        self.prob = pulp.LpProblem("MasterProblem", pulp.LpMinimize)

        # vartype represents whether or not the variables are relaxed
        if self.relax:
            self.vartype = pulp.LpContinuous
        else:
            self.vartype = pulp.LpInteger

        # create variables, one per route
        self.add_route_selection_variables()

        # if dropping nodes is allowed
        if self.drop_penalty:
            self.add_drop_variables()

        # if frequencies, dummy variables are needed to find initial solution
        if self.periodic:
            self.add_artificial_variables()

        # cost function
        self.add_cost_function()

        # visit each node once (or periodically if frequencies are given)
        self.add_set_covering_constraints()

        # bound number of vehicles
        if self.num_vehicles:
            self.add_bound_vehicles()

    def add_cost_function(self):
        """
        Sum of transport costs.
        If dropping nodes is allowed, penalties are added to the cost function.
        """
        transport_cost = pulp.lpSum(
            [self.y[r.graph["name"]] * r.graph["cost"] for r in self.routes]
        )
        if self.drop_penalty:
            dropping_visits_cost = self.drop_penalty * pulp.lpSum(
                [self.drop[v] for v in self.drop]
            )
        else:
            dropping_visits_cost = 0
        if self.periodic:
            dummy_cost = 1e10 * pulp.lpSum([self.dummy[v] for v in self.dummy])
        else:
            dummy_cost = 0
        self.prob += transport_cost + dropping_visits_cost + dummy_cost

    def add_set_covering_constraints(self):
        """
        All vertices must be visited exactly once, or periodically if frequencies are given.
        If dropping nodes is allowed, the drop variable is activated (as well as a penalty is the cost function).
        """
        for v in self.G.nodes():
            if (
                v not in ["Source", "Sink"]
                and "depot_from" not in self.G.nodes[v]
                and "depot_to" not in self.G.nodes[v]
            ):
                if self.periodic:
                    right_hand_term = self.G.nodes[v]["frequency"]
                elif self.drop_penalty:
                    right_hand_term = 1 - self.drop[v]
                else:
                    right_hand_term = 1

                visit_node = pulp.lpSum(
                    [self.y[r.graph["name"]] for r in self.routes_with_node[v]]
                )
                if self.periodic:
                    if v in self.dummy:
                        visit_node += self.dummy[v]
                if self.relax:
                    # set covering constraints
                    # cuts the dual space in half
                    self.prob += visit_node >= right_hand_term, "visit_node_%s" % v
                else:
                    # set partitioning constraints
                    self.prob += visit_node == right_hand_term, "visit_node_%s" % v

    def add_route_selection_variables(self):
        """
        Boolean variable.
        y[r] takes value 1 if and only if route r is selected.
        """
        self.y = pulp.LpVariable.dicts(
            "y",
            [r.graph["name"] for r in self.routes],
            lowBound=0,
            upBound=1,
            cat=self.vartype,
        )

    def add_drop_variables(self):
        """
        Boolean variable.
        drop[v] takes value 1 if and only if node v is dropped.
        """
        self.drop = pulp.LpVariable.dicts(
            "drop",
            [v for v in self.G.nodes() if self.G.nodes[v]["demand"] > 0],
            lowBound=0,
            upBound=1,
            cat=self.vartype,
        )

    def add_artificial_variables(self):
        """Continuous variable used for finding initial feasible solution."""
        self.dummy = pulp.LpVariable.dicts(
            "artificial",
            [v for v in self.G.nodes() if self.G.nodes[v]["frequency"] > 1],
            lowBound=0,
            upBound=None,
            cat=pulp.LpContinuous,
        )

    def get_duals(self):
        """Gets the dual values of each constraint of the master problem.

        Returns:
            dict: Duals with constraint names as keys and dual variables as values
        """
        duals = {}
        # set covering duals
        for v in self.G.nodes():
            if (
                v not in ["Source", "Sink"]
                and "depot_from" not in self.G.nodes[v]
                and "depot_to" not in self.G.nodes[v]
            ):
                constr_name = "visit_node_%s" % v
                duals[v] = self.prob.constraints[constr_name].pi
        # num vehicles dual
        if self.num_vehicles:
            duals["upper_bound_vehicles"] = {}
            for k in range(len(self.num_vehicles)):
                duals["upper_bound_vehicles"][k] = self.prob.constraints[
                    "upper_bound_vehicles_%s" % k
                ].pi
        return duals

    def add_bound_vehicles(self):
        """Adds constraint such that number of active variables <= num_vehicles."""
        for k in range(len(self.num_vehicles)):
            self.prob += (
                pulp.lpSum(
                    [
                        self.y[r.graph["name"]]
                        for r in self.routes
                        if r.graph["vehicle_type"] == k
                    ]
                )
                <= self.num_vehicles[k],
                "upper_bound_vehicles_%s" % k,
            )
