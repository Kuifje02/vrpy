import pulp
import logging

logger = logging.getLogger(__name__)


class _Schedule:
    """
    Scheduling algorithm for the Periodic CVRP.

    Args:
        G (DiGraph): Graph on which algorithm is run.
        time_span (int): Time horizon.
        routes (list): List of best routes previously computed (VehicleRoutingProblem.best_routes).
        route_type (dict): Key: route ID; Value: vehicle_type (VehicleRoutingProblem.best_routes_type).
        num_vehicles (int, optional): Maximum number of vehicles available. Defaults to None.
    """

    def __init__(
        self, G, time_span, routes, route_type, num_vehicles=None, solver="cbc"
    ):
        self.G = G
        self.time_span = time_span
        self.routes = routes
        self.route_type = route_type
        self.num_vehicles = num_vehicles
        self.solver = solver

        # create problem
        self.prob = pulp.LpProblem("Schedule", pulp.LpMinimize)
        # create variables
        # y[r][t] = 1 <=> route r is scheduled on day t
        self.y = pulp.LpVariable.dicts(
            "y",
            (self.routes, [t for t in range(self.time_span)],),
            lowBound=0,
            upBound=1,
            cat=pulp.LpBinary,
        )
        # max load
        self.load_max = pulp.LpVariable("load_max", lowBound=0, cat=pulp.LpContinuous)
        # min load
        self.load_min = pulp.LpVariable("load_min", lowBound=0, cat=pulp.LpContinuous)

    def solve(self, time_limit):
        """Formulates the scheduling problem as a linear program and solves it."""

        self._formulate()
        self._solve(time_limit)
        # self.prob.writeLP("schedule.lp")
        logger.debug("Status: %s" % pulp.LpStatus[self.prob.status])
        logger.debug("Objective %s" % pulp.value(self.prob.objective))

    def _formulate(self):
        """Scheduling problem as LP."""

        # objective function : balance load over planning planning period
        self.prob += self.load_max - self.load_min

        # load_max definition
        for t in range(self.time_span):
            self.prob += (
                pulp.lpSum([self.y[r][t] for r in self.routes]) <= self.load_max,
                "load_max_%s" % t,
            )

        # load_min definition
        for t in range(self.time_span):
            self.prob += (
                pulp.lpSum([self.y[r][t] for r in self.routes]) >= self.load_min,
                "load_min_%s" % t,
            )

        # one day per route
        for r in self.routes:
            self.prob += (
                pulp.lpSum([self.y[r][t] for t in range(self.time_span)]) == 1,
                "schedule_%s" % r,
            )
        # at most one visit per day per customer
        for t in range(self.time_span):
            for v in self.G.nodes():
                if self.G.nodes[v]["demand"] > 0:
                    self.prob += (
                        pulp.lpSum(
                            [self.y[r][t] for r in self.routes if v in self.routes[r]]
                        )
                        <= 1,
                        "day_%s_max_visit_%s" % (t, v),
                    )
        # max fleet per day
        if self.num_vehicles:
            for k in range(len(self.num_vehicles)):
                for t in range(self.time_span):
                    self.prob += (
                        pulp.lpSum(
                            [
                                self.y[r][t]
                                for r in self.routes
                                if self.route_type[r] == k
                            ]
                        )
                        <= self.num_vehicles[k],
                        "max_fleet_type_%s_day_%s" % (k, t),
                    )

    def _solve(self, time_limit):
        if self.solver == "cbc":
            self.prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
        elif self.solver == "cplex":
            self.prob.solve(pulp.CPLEX_CMD(msg=False, timelimit=time_limit))
        elif self.solver == "gurobi":
            gurobi_options = []
            if time_limit is not None:
                gurobi_options.append(("TimeLimit", time_limit,))
            self.prob.solve(pulp.GUROBI(msg=False, options=gurobi_options))

    @property
    def routes_per_day(self):
        """Returns a dict with keys the day and values the route IDs scheduled this day."""
        day = {}
        if pulp.LpStatus[self.prob.status] == "Optimal":
            for r in self.routes:
                for t in range(self.time_span):
                    if pulp.value(self.y[r][t]) > 0.9:
                        if t not in day:
                            day[t] = [r]
                        else:
                            day[t].append(r)
        return day
