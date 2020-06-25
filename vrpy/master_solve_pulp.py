import logging

from networkx import shortest_path
import pulp

from vrpy.masterproblem import MasterProblemBase

logger = logging.getLogger(__name__)


class MasterSolvePulp(MasterProblemBase):
    """
    Solves the master problem for the column generation procedure.

    Inherits problem parameters from MasterProblemBase
    """

    def __init__(self, *args, solver):
        super(MasterSolvePulp, self).__init__(*args)
        # create problem
        self.prob = pulp.LpProblem("MasterProblem", pulp.LpMinimize)
        # objective
        self.objective = pulp.LpConstraintVar("objective")
        # variables
        self.y = {}  # route selection variable
        self.drop = {}  # dropping variable
        self.dummy = {}  # dummy variable
        self.dummy_bound = {}  # dummy variable for vehicle bound cost
        # constrs
        self.set_covering_constrs = {}
        self.vehicle_bound_constrs = {}
        self.drop_penalty_constrs = {}
        # Diving attributes
        self._tabu_list = []
        self._formulate()
        self._set_solver(solver)

    def solve(self, relax):
        # self.prob.writeLP("master.lp")
        self._solve(relax)
        logger.debug("master problem")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective: %s" % pulp.value(self.prob.objective))

        if pulp.LpStatus[self.prob.status] != "Optimal":
            raise Exception("problem " + str(pulp.LpStatus[self.prob.status]))
        if relax:
            for r in self.routes:
                if pulp.value(self.y[r.graph["name"]]) > 0.5:
                    logger.debug("route %s selected" % r.graph["name"])
            duals = self.get_duals()
            logger.debug("duals : %s" % duals)
            return duals, self.prob.objective.value()

        else:
            return self._get_total_cost_and_routes(relax=False)

    def solve_and_dive(self, max_depth=3, max_discrepancy=1):
        """
        Implements diving algorithm with Limited Discrepancy Search
        Parameters as suggested by the authors. This only fixes one column.
        `Sadykov et al. (2019)`_.

        .. _Sadykov et al. (2019): https://pubsonline.informs.org/doi/abs/10.1287/ijoc.2018.0822
        """
        self._solve(relax=True)

        depth = 0
        tabu_list = []
        stop_diving = True
        relax = self.prob.deepcopy()
        constrs = {}
        while depth <= max_depth and len(tabu_list) <= max_discrepancy:
            non_integer_vars = list(
                var for var in relax.variables()
                if abs(var.varValue - round(var.varValue)) != 0)
            # All non-integer variables not already fixed in this or any
            # iteration of the diving heuristic
            vars_to_fix = [
                var for var in non_integer_vars
                if var.name not in self._tabu_list and var.name not in tabu_list
            ]
            if vars_to_fix:
                # If non-integer variables not already fixed and
                # max_discrepancy not violated
                stop_diving = False

                var_to_fix = min(
                    vars_to_fix,
                    key=lambda x: abs(x.varValue - round(x.varValue)))
                value_to_fix = 1
                value_previous = var_to_fix.varValue

                name_le = "fix_{}_LE".format(var_to_fix.name)
                name_ge = "fix_{}_GE".format(var_to_fix.name)
                constrs[name_le] = pulp.LpConstraint(var_to_fix,
                                                     pulp.LpConstraintLE,
                                                     name=name_le,
                                                     rhs=value_to_fix)
                constrs[name_ge] = pulp.LpConstraint(var_to_fix,
                                                     pulp.LpConstraintGE,
                                                     name=name_ge,
                                                     rhs=value_to_fix)

                relax += constrs[name_le]  # add <= constraint
                relax += constrs[name_ge]  # add >= constraint
                relax.solve()
                # if not optimal status code from :
                # https://github.com/coin-or/pulp/blob/master/pulp/constants.py#L45-L57
                if relax.status != 1 or all(
                        abs(v.varValue - round(v.varValue)) == 0
                        for v in relax.variables()):
                    stop_diving = True
                    break
                if len(tabu_list) >= max_discrepancy:
                    break
                tabu_list.append(var_to_fix.name)
                depth += 1
                self.prob.extend(constrs)
                logger.info("fixed %s with previous value %s", var_to_fix.name,
                            value_previous)
            else:
                break
        logger.debug("Ran diving with LDS and fixed %s vars", len(tabu_list))
        self._tabu_list.extend(tabu_list)
        return self._get_total_cost_and_routes(relax=True), stop_diving

    def update(self, new_route):
        """Add new column.
        """
        self._add_route_selection_variable(new_route)

    def get_duals(self):
        """Gets the dual values of each constraint of the master problem.

        Returns:
            dict: Duals with constraint names as keys and dual variables as values
        """
        duals = {}
        # set covering duals
        for node in self.G.nodes():
            if (node not in ["Source", "Sink"] and
                    "depot_from" not in self.G.nodes[node] and
                    "depot_to" not in self.G.nodes[node]):
                constr_name = "visit_node_%s" % node
                duals[node] = self.prob.constraints[constr_name].pi
        # num vehicles dual
        if self.num_vehicles and not self.periodic:
            duals["upper_bound_vehicles"] = {}
            for k in range(len(self.num_vehicles)):
                duals["upper_bound_vehicles"][k] = self.prob.constraints[
                    "upper_bound_vehicles_%s" % k].pi
        return duals

    # Private methods to solve and output #

    def _solve(self, relax: bool):
        # Set variable types
        for var in self.prob.variables():
            if relax:
                var.cat = pulp.LpContinuous
            else:
                var.cat = pulp.LpInteger
                if "artificial_bound_" in var.name:
                    var.upBound = 0
                    var.lowBound = 0
        # Solve with solver already set
        self.prob.resolve()

    def _set_solver(self, solver):
        if solver == "cbc":
            self.prob.setSolver(
                pulp.PULP_CBC_CMD(
                    msg=0,
                    maxSeconds=self.time_limit,
                    options=["startalg", "barrier", "crossover", "0"],
                ))
        elif solver == "cplex":
            self.prob.setSolver(
                pulp.CPLEX_CMD(
                    msg=0,
                    timelimit=self.time_limit,
                    options=["set lpmethod 4", "set barrier crossover -1"],
                ))
        elif solver == "gurobi":
            gurobi_options = [
                ("Method", 2),  # 2 = barrier
                ("Crossover", 0),
            ]
            # Only specify time limit if given (o.w. errors)
            if self.time_limit is not None:
                gurobi_options.append((
                    "TimeLimit",
                    self.time_limit,
                ))
            self.prob.setSolver(pulp.GUROBI(msg=0, options=gurobi_options))

    def _get_total_cost_and_routes(self, relax: bool):
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
        total_cost = self.prob.objective.value()
        if not relax and self.drop_penalty and len(self.dropped_nodes) > 0:
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

        self._add_set_covering_constraints()

        if self.num_vehicles and not self.periodic:
            self._add_bound_vehicles()

        # Add variables #
        # Route selection variables
        for route in self.routes:
            self._add_route_selection_variable(route)
        # if dropping nodes is allowed
        if self.drop_penalty:
            self._add_drop_variables()

        # if frequencies, dummy variables are needed to find initial solution
        if self.periodic:
            self._add_artificial_variables()
        # Add constraints to problem
        for k in self.set_covering_constrs:
            self.prob += self.set_covering_constrs[k]
        for k in self.vehicle_bound_constrs:
            self.prob += self.vehicle_bound_constrs[k]

        # Add dummy_vehicle variables
        self._add_vehicle_dummy_variables()

        # Set objective function
        self.prob.sense = pulp.LpMinimize
        self.prob.setObjective(self.objective)

    def _add_set_covering_constraints(self):
        """
        All vertices must be visited exactly once, or periodically if
        frequencies are given.
        If dropping nodes is allowed, the drop variable is activated
        (as well as a penalty is the cost function).
        """
        for node in self.G.nodes():
            if (node not in ["Source", "Sink"] and
                    "depot_from" not in self.G.nodes[node] and
                    "depot_to" not in self.G.nodes[node]):
                # Set RHS
                if self.periodic:
                    right_hand_term = self.G.nodes[node]["frequency"]
                else:
                    right_hand_term = 1
                # Save set covering constraints
                self.set_covering_constrs[node] = pulp.LpConstraintVar(
                    "visit_node_%s" % node, pulp.LpConstraintGE,
                    right_hand_term)

    def _add_route_selection_variable(self, route):
        self.y[route.graph["name"]] = pulp.LpVariable(
            "y{}".format(route.graph["name"]),
            lowBound=0,
            upBound=1,
            cat=pulp.LpInteger,
            e=(pulp.lpSum(self.set_covering_constrs[r]
                          for r in route.nodes()
                          if r not in ["Source", "Sink"]) +
               pulp.lpSum(self.vehicle_bound_constrs[k]
                          for k in range(len(self.num_vehicles))
                          if route.graph["vehicle_type"] == k) +
               route.graph["cost"] * self.objective))

    def _add_vehicle_dummy_variables(self):
        for key in range(len(self.num_vehicles)):
            self.dummy_bound[key] = pulp.LpVariable(
                "artificial_bound_%s" % key,
                lowBound=0,
                upBound=None,
                cat=pulp.LpContinuous,
                e=((-1) * self.vehicle_bound_constrs[key] +
                   1e10 * self.objective))

    def _add_drop_variables(self):
        """
        Boolean variable.
        drop[v] takes value 1 if and only if node v is dropped.
        """
        for node in self.G.nodes():
            if self.G.nodes[node]["demand"] > 0 and node != "Source":
                self.drop[node] = pulp.LpVariable(
                    "drop_%s" % node,
                    lowBound=0,
                    upBound=1,
                    cat=pulp.LpInteger,
                    e=(self.drop_penalty * self.objective +
                       self.set_covering_constrs[node]))

    def _add_artificial_variables(self):
        """Continuous variable used for finding initial feasible solution."""
        for node in self.G.nodes():
            if self.G.nodes[node]["frequency"] > 1 and node != "Source":
                self.dummy[node] = pulp.LpVariable(
                    "periodic_%s" % node,
                    lowBound=0,
                    upBound=None,
                    cat=pulp.LpInteger,
                    e=(1e10 * self.objective + self.set_covering_constrs[node]))

    def _add_bound_vehicles(self):
        """Adds empty constraints and sets the right hand side"""
        for k in range(len(self.num_vehicles)):
            self.vehicle_bound_constrs[k] = pulp.LpConstraintVar(
                "upper_bound_vehicles_%s" % k, pulp.LpConstraintLE,
                self.num_vehicles[k])
