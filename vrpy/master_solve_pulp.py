import pulp
import logging
from masterproblem import MasterProblemBase
from networkx import shortest_path

logger = logging.getLogger(__name__)


class MasterSolvePulp(MasterProblemBase):
    """
    Solves the master problem for the column generation procedure.

    Inherits problem parameters from MasterProblemBase
    """

    def solve(self):
        self.formulate()
        self.prob.solve()
        # self.prob.writeLP("masterprob.lp")
        # if you have CPLEX
        # self.prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
        logger.debug("master problem")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective: %s" % pulp.value(self.prob.objective))

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
                    logger.info(
                        "%s cost %s"
                        % (shortest_path(r, "Source", "Sink"), r.graph["cost"])
                    )
                    best_routes.append(r)
            if self.drop_penalty:
                dropped_nodes = [v for v in self.drop if pulp.value(self.drop[v]) > 0.5]
            total_cost = pulp.value(self.prob.objective)
            if not self.relax and self.drop_penalty and len(dropped_nodes) > 0:
                logger.info("dropped nodes : %s" % dropped_nodes)
                total_cost -= len(dropped_nodes) * 1000
            logger.info("total cost = %s" % total_cost)
            return pulp.value(self.prob.objective), best_routes

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
        _routes = []
        for r in self.routes:
            _routes.append(r.graph["name"])
        self.y = pulp.LpVariable.dicts(
            "y", _routes, lowBound=0, upBound=1, cat=self.vartype
        )

        # if dropping nodes is allowed
        if self.drop_penalty:
            self.add_drop_variables()

        # cost function
        self.add_cost_function()

        # visit each node once
        self.add_set_covering_constraints()

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
        self.prob += transport_cost + dropping_visits_cost

    def add_set_covering_constraints(self):
        """
        All vertices must be visited exactly once,
        except if dropping nodes is allowed. In this
        case the drop variable is activated (as well as
        a penalty is the cost function).
        """
        for v in self.G.nodes():
            if (
                v not in ["Source", "Sink"]
                and "depot_from" not in self.G.nodes[v]
                and "depot_to" not in self.G.nodes[v]
            ):
                right_hand_term = 1
                if self.drop_penalty:
                    right_hand_term -= self.drop[v]

                self.prob += (
                    pulp.lpSum(
                        [self.y[r.graph["name"]] for r in self.routes if v in r.nodes()]
                    )
                    == right_hand_term,
                    "visit_node_%s" % v,
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
        return duals
