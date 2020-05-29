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

    def solve(self):
        self._formulate()
        self._solve()
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
            return self._get_total_cost_and_routes()

    def solve_and_dive(self, max_depth=3, max_discrepancy=3):
        """
        Implements diving algorithm with Limited Discrepancy Search.
        From : `Sadykov et al. (2019)`_.

        .. _Sadykov et al. (2019): https://pubsonline.informs.org/doi/abs/10.1287/ijoc.2018.0822
        """
        self._formulate()
        self._solve()
        if self.prob.status != 1:
            return

        depth = 0
        tabu_list = []
        while depth <= max_depth and len(tabu_list) <= max_discrepancy:
            a_relax_vars = list(var for var in self.prob.variables()
                                if abs(var.varValue - round(var.varValue)) != 0)
            vars_to_fix = [
                var for var in a_relax_vars if var.name not in tabu_list
            ]
            if vars_to_fix:
                var_to_fix = min(
                    vars_to_fix,
                    key=lambda x: abs(x.varValue - round(x.varValue)))
                value_to_fix = 1
                self.prob += var_to_fix <= value_to_fix
                self.prob += var_to_fix >= value_to_fix
                self._solve()
                # if NOT optimal.
                # status code from : https://github.com/coin-or/pulp/blob/master/pulp/constants.py#L45-L57
                if self.prob.status != 1:
                    logger.debug(" Ran diving with LDS and fixed %s vars",
                                 len(tabu_list))
                    break
                tabu_list.append(var_to_fix.name)
                depth += 1
            else:
                logger.debug(" Ran diving with LDS and fixed %s vars",
                             len(tabu_list))
                break
        self._solve()
        return self._get_total_cost_and_routes()

    def get_duals(self):
        """Gets the dual values of each constraint of the master problem.

        Returns:
            dict: Duals with constraint names as keys and dual variables as values
        """
        duals = {}
        # set covering duals
        for v in self.G.nodes():
            if (v not in ["Source", "Sink"] and
                    "depot_from" not in self.G.nodes[v] and
                    "depot_to" not in self.G.nodes[v]):
                constr_name = "visit_node_%s" % v
                duals[v] = self.prob.constraints[constr_name].pi
        # num vehicles dual
        if self.num_vehicles:
            duals["upper_bound_vehicles"] = {}
            for k in range(len(self.num_vehicles)):
                duals["upper_bound_vehicles"][k] = self.prob.constraints[
                    "upper_bound_vehicles_%s" % k].pi
        return duals

    # Private methods to solve and output #

    def _solve(self):
        if self.time_limit and self.time_limit <= 0:
            return
        if self.solver == "cbc":
            self.prob.solve(pulp.PULP_CBC_CMD(maxSeconds=self.time_limit))
        elif self.solver == "cplex":
            self.prob.solve(pulp.solvers.CPLEX_CMD(timelimit=self.time_limit))
        elif self.solver == "gurobi":
            gurobi_options = [("TimeLimit", self.time_limit)]
            self.prob.solve(pulp.solvers.GUROBI_CMD(options=gurobi_options))

    def _get_total_cost_and_routes(self):
        best_routes = []
        for r in self.routes:
            val = pulp.value(self.y[r.graph["name"]])
            if val is not None and val > 0:
                logger.debug("%s cost %s load %s" % (
                    shortest_path(r, "Source", "Sink"),
                    r.graph["cost"],
                    sum([self.G.nodes[v]["demand"] for v in r.nodes()]),
                ))
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

    # Private methods for formulating the problem #

    def _formulate(self):
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
        self._add_route_selection_variables()

        # if dropping nodes is allowed
        if self.drop_penalty:
            self._add_drop_variables()

        # if frequencies, dummy variables are needed to find initial solution
        if self.periodic:
            self._add_artificial_variables()

        # cost function
        self._add_cost_function()

        # visit each node once (or periodically if frequencies are given)
        self._add_set_covering_constraints()

        # bound number of vehicles
        if self.num_vehicles:
            self._add_bound_vehicles()

    def _add_cost_function(self):
        """
        Sum of transport costs.
        If dropping nodes is allowed, penalties are added to the cost function.
        """
        transport_cost = pulp.lpSum(
            [self.y[r.graph["name"]] * r.graph["cost"] for r in self.routes])
        if self.drop_penalty:
            dropping_visits_cost = self.drop_penalty * pulp.lpSum(
                [self.drop[v] for v in self.drop])
        else:
            dropping_visits_cost = 0
        if self.periodic:
            dummy_cost = 1e10 * pulp.lpSum([self.dummy[v] for v in self.dummy])
        else:
            dummy_cost = 0
        self.prob += transport_cost + dropping_visits_cost + dummy_cost

    def _add_set_covering_constraints(self):
        """
        All vertices must be visited exactly once, or periodically if frequencies are given.
        If dropping nodes is allowed, the drop variable is activated (as well as a penalty is the cost function).
        """
        for v in self.G.nodes():
            if (v not in ["Source", "Sink"] and
                    "depot_from" not in self.G.nodes[v] and
                    "depot_to" not in self.G.nodes[v]):
                if self.periodic:
                    right_hand_term = self.G.nodes[v]["frequency"]
                elif self.drop_penalty:
                    right_hand_term = 1 - self.drop[v]
                else:
                    right_hand_term = 1

                visit_node = pulp.lpSum(
                    [self.y[r.graph["name"]] for r in self.routes_with_node[v]])
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

    def _add_route_selection_variables(self):
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

    def _add_drop_variables(self):
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

    def _add_artificial_variables(self):
        """Continuous variable used for finding initial feasible solution."""
        self.dummy = pulp.LpVariable.dicts(
            "artificial",
            [v for v in self.G.nodes() if self.G.nodes[v]["frequency"] > 1],
            lowBound=0,
            upBound=None,
            cat=pulp.LpContinuous,
        )

    def _add_bound_vehicles(self):
        """Adds constraint such that number of active variables <= num_vehicles."""
        for k in range(len(self.num_vehicles)):
            self.prob += (
                pulp.lpSum([
                    self.y[r.graph["name"]]
                    for r in self.routes
                    if r.graph["vehicle_type"] == k
                ]) <= self.num_vehicles[k],
                "upper_bound_vehicles_%s" % k,
            )
