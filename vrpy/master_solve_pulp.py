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
        # self.prob.solve()
        # if you have CPLEX
        # self.prob.writeLP("masterprob.lp")
        self.prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
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
                if val > 0:
                    logger.info(
                        "%s cost %s"
                        % (shortest_path(r, "Source", "Sink"), r.graph["cost"])
                    )
                    best_routes.append(r)
            logger.info("total cost = %s" % pulp.value(self.prob.objective))
            return pulp.value(self.prob.objective), best_routes

    def formulate(self):
        # create problem
        self.prob = pulp.LpProblem("MasterProblem", pulp.LpMinimize)

        # vartype represents whether or not the variables are relaxed
        if self.relax:
            vartype = pulp.LpContinuous
        else:
            vartype = pulp.LpInteger

        # create variables
        _routes = []
        for r in self.routes:
            _routes.append(r.graph["name"])
        self.y = pulp.LpVariable.dicts("y", _routes, lowBound=0, upBound=1, cat=vartype)

        # cost function
        self.prob += pulp.lpSum(
            [self.y[r.graph["name"]] * r.graph["cost"] for r in self.routes]
        )

        # visit each node once
        for v in self.G.nodes():
            if (
                v not in ["Source", "Sink"]
                and "depot_from" not in self.G.nodes[v]
                and "depot_to" not in self.G.nodes[v]
            ):
                self.prob += (
                    pulp.lpSum(
                        [self.y[r.graph["name"]] for r in self.routes if v in r.nodes()]
                    )
                    == 1,
                    "visit_node_%s" % v,
                )

    def get_duals(self):
        """Gets the dual values of each constraint of the master problem.

        Returns:
            dict: Duals with constraint names as keys and dual variables as values
        """
        duals = {}
        for v in self.G.nodes():
            if (
                v not in ["Source", "Sink"]
                and "depot_from" not in self.G.nodes[v]
                and "depot_to" not in self.G.nodes[v]
            ):
                constr_name = "visit_node_%s" % v
                duals[v] = self.prob.constraints[constr_name].pi
        return duals
