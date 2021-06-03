import logging
from math import floor
from numpy import zeros
from networkx import DiGraph, add_path
from cspy import BiDirectional, REFCallback
from vrpy.subproblem import _SubProblemBase

logger = logging.getLogger(__name__)


class _MyREFCallback(REFCallback):
    """
    Custom REFs for time, time windows, and/or distribution collection.
    Based on Righini and Salani (2006).
    """

    def __init__(self, max_res, time_windows, distribution_collection, T, resources):
        REFCallback.__init__(self)
        # Set attributes for use in REF functions
        self._max_res = max_res
        self._time_windows = time_windows
        self._distribution_collection = distribution_collection
        self._T = T
        self._resources = resources
        # Set later
        self._sub_G = None
        self._source_id = None
        self._sink_id = None

    def REF_fwd(self, cumul_res, tail, head, edge_res, partial_path, cumul_cost):
        new_res = list(cumul_res)
        i, j = tail, head
        # stops / monotone resource
        new_res[0] += 1
        # load
        new_res[1] += self._sub_G.nodes[j]["demand"]
        # time
        # Service times
        theta_i = self._sub_G.nodes[i]["service_time"]
        # theta_j = self._sub_G.nodes[j]["service_time"]
        # theta_t = self._sub_G.nodes[self._sink_id]["service_time"]
        # Travel times
        travel_time_ij = self._sub_G.edges[i, j]["time"]
        # try:
        #    travel_time_jt = self._sub_G.edges[j, self._sink_id]["time"]
        # except KeyError:
        #    travel_time_jt = 0
        # Time windows
        # Lower
        a_j = self._sub_G.nodes[j]["lower"]
        # a_t = self._sub_G.nodes[self._sink_id]["lower"]
        # Upper
        b_j = self._sub_G.nodes[j]["upper"]
        # b_t = self._sub_G.nodes[self._sink_id]["upper"]

        new_res[2] = max(new_res[2] + theta_i + travel_time_ij, a_j)

        # time-window feasibility resource
        if not self._time_windows or (new_res[2] <= b_j):
            # and new_res[2] < self._T - a_j - theta_j and
            # a_t <= new_res[2] + travel_time_jt + theta_t <= b_t):
            # if not self._time_windows or (
            #         new_res[2] <= b_j and new_res[2] < self._T - a_j - theta_j and
            #         a_t <= new_res[2] + travel_time_jt + theta_t <= b_t):
            new_res[3] = 0
        else:
            new_res[3] = 1

        if self._distribution_collection:
            # Pickup
            new_res[4] += self._sub_G.nodes[j]["collect"]
            # Delivery
            new_res[5] = max(new_res[5] + self._sub_G.nodes[j]["demand"], new_res[4])
        return new_res

    def REF_bwd(self, cumul_res, tail, head, edge_res, partial_path, cumul_cost):
        new_res = list(cumul_res)
        i, j = tail, head

        # monotone resource
        new_res[0] -= 1
        # load
        new_res[1] += self._sub_G.nodes[i]["demand"]
        # Get relevant service times (thetas) and travel time
        # Service times
        theta_i = self._sub_G.nodes[i]["service_time"]
        theta_j = self._sub_G.nodes[j]["service_time"]
        # theta_s = self._sub_G.nodes[self._source_id]["service_time"]
        # Travel times
        travel_time_ij = self._sub_G.edges[i, j]["time"]
        # try:
        #    travel_time_si = self._sub_G.edges[self._source_id, i]["time"]
        # except KeyError:
        #    travel_time_si = 0
        # Lower time windows
        # a_i = self._sub_G.nodes[i]["lower"]
        # a_j = self._sub_G.nodes[j]["lower"]
        # a_s = self._sub_G.nodes[self._source_id]["lower"]
        # Upper time windows
        b_i = self._sub_G.nodes[i]["upper"]
        b_j = self._sub_G.nodes[j]["upper"]
        # b_s = self._sub_G.nodes[self._source_id]["upper"]

        new_res[2] = max(new_res[2] + theta_j + travel_time_ij, self._T - b_i - theta_i)

        # time-window feasibility
        if not self._time_windows or (new_res[2] <= b_j):
            # and new_res[2] < self._T - a_i - theta_i and
            #         a_s <= new_res[2] + theta_s + travel_time_si <= b_s):
            # if not self._time_windows or (
            #         new_res[2] <= self._T - a_j and
            #         new_res[2] < self._T - a_i - theta_i and
            #         a_s <= new_res[2] + theta_s + travel_time_si <= b_s):
            new_res[3] = 0
        else:
            new_res[3] = 1

        if self._distribution_collection:
            # Delivery
            new_res[5] += new_res[5] + self._sub_G.nodes[i]["demand"]
            # Pickup
            new_res[4] = max(new_res[5], new_res[4] + self._sub_G.nodes[i]["collect"])
        return new_res

    def REF_join(self, fwd_resources, bwd_resources, tail, head, edge_res):
        """
        Appropriate joining of forward and backward resources.
        """
        fwd_res = list(fwd_resources)
        bwd_res = list(bwd_resources)
        final_res = [0] * len(self._resources)

        i, j = tail, head

        # Get relevant service times (thetas) and travel time
        theta_i = self._sub_G.nodes[i]["service_time"]
        theta_j = self._sub_G.nodes[j]["service_time"]
        travel_time = self._sub_G.edges[i, j]["time"]

        # Invert monotone resource
        bwd_res[0] = self._max_res[0] - bwd_res[0]
        # Fill in final res
        # Monotone / stops
        final_res[0] = fwd_res[0] + bwd_res[0] + 1
        # Load
        final_res[1] = fwd_res[1] + bwd_res[1]
        # time
        final_res[2] = fwd_res[2] + theta_i + travel_time + theta_j + bwd_res[2]
        # Time windows
        if not self._time_windows or final_res[2] <= self._T:
            final_res[3] = fwd_res[3] + bwd_res[3]
        else:
            final_res[3] = 1.0

        if self._distribution_collection:
            final_res[4] = fwd_res[4] + bwd_res[4]
            final_res[5] = fwd_res[5] + bwd_res[5]
        return final_res


class _SubProblemCSPY(_SubProblemBase):
    """
    Solves the sub problem for the column generation procedure with cspy;
    attemps to find routes with negative reduced cost.

    Inherits problem parameters from `SubproblemBase`
    """

    def __init__(self, *args, exact):
        """Initializes resources."""
        # Pass arguments to base
        super(_SubProblemCSPY, self).__init__(*args)
        self.exact = exact
        # Resource names
        self.resources = [
            "stops/mono",
            "load",
            "time",
            "time windows",
            "collect",
            "deliver",
        ]
        # Set number of resources as attribute of graph
        self.sub_G.graph["n_res"] = len(self.resources)
        # Default lower and upper bounds
        self.min_res = [0] * len(self.resources)
        # Add upper bounds for mono, stops, load and time, and time windows
        total_demand = sum([self.sub_G.nodes[v]["demand"] for v in self.sub_G.nodes()])
        self.max_res = [
            floor(len(self.sub_G.nodes()) / 2),  # stop/mono
            total_demand,  # load
            sum(
                [self.sub_G.edges[u, v]["time"] for u, v in self.sub_G.edges()]
            ),  # time
            1,  # time windows
            total_demand,  # pickup
            total_demand,  # deliver
        ]
        # Initialize cspy edge attributes
        for edge in self.sub_G.edges(data=True):
            edge[2]["res_cost"] = zeros(len(self.resources))
        # Initialize max feasible arrival time
        self.T = 0
        self.total_cost = None

    # @profile
    def solve(self, time_limit):
        """
        Solves the subproblem with cspy.
        Time limit is reduced by 0.5 seconds as a safety window.

        Resolves until:
        1. heuristic algorithm gives a new route (column with -ve reduced cost);
        2. exact algorithm gives a new route;
        3. neither heuristic nor exact give a new route.
        """
        if not self.run_subsolve:
            return self.routes, False

        self.formulate()
        logger.debug("resources = {}".format(self.resources))
        logger.debug("min res = {}".format(self.min_res))
        logger.debug("max res = {}".format(self.max_res))

        more_routes = False

        my_callback = self.get_REF()
        while True:
            if self.exact:
                alg = BiDirectional(
                    self.sub_G,
                    self.max_res,
                    self.min_res,
                    direction="both",
                    time_limit=time_limit - 0.5 if time_limit else None,
                    elementary=True,
                    REF_callback=my_callback,
                )
            else:
                alg = BiDirectional(
                    self.sub_G,
                    self.max_res,
                    self.min_res,
                    threshold=-1,
                    direction="both",
                    time_limit=time_limit - 0.5 if time_limit else None,
                    elementary=True,
                    REF_callback=my_callback,
                )

            # Pass processed graph
            if my_callback is not None:
                my_callback._sub_G = alg.G
                my_callback._source_id = alg._source_id
                my_callback._sink_id = alg._sink_id
            alg.run()
            logger.debug("subproblem")
            logger.debug("cost = %s", alg.total_cost)
            logger.debug("resources = %s", alg.consumed_resources)
            if alg.total_cost is not None and alg.total_cost < -(1e-3):
                more_routes = True
                self.add_new_route(alg.path)
                logger.debug("new route %s", alg.path)
                logger.debug("reduced cost = %s", alg.total_cost)
                logger.debug("real cost = %s", self.total_cost)
                break
            # If not already solved exactly
            elif not self.exact:
                # Solve exactly from here on
                self.exact = True
            # Solved heuristically and exactly and no more routes
            # Or time out
            else:
                break
        return self.routes, more_routes

    def formulate(self):
        """Updates max_res depending on which contraints are active."""
        # Problem specific constraints
        if self.num_stops:
            self.add_max_stops()
        else:
            self.add_monotone()
        if self.load_capacity:
            self.add_max_load()
        if self.duration:
            self.add_max_duration()
        if self.time_windows:
            if not self.duration:
                # Update upper bound for duration
                self.max_res[2] = 1 + self.sub_G.nodes["Sink"]["upper"]
            # Time windows feasibility
            self.max_res[3] = 0
            # Maximum feasible arrival time
            self.T = max(
                self.sub_G.nodes[v]["upper"]
                + self.sub_G.nodes[v]["service_time"]
                + self.sub_G.edges[v, "Sink"]["time"]
                for v in self.sub_G.predecessors("Sink")
            )

        if self.load_capacity and self.distribution_collection:
            self.max_res[4] = self.load_capacity[self.vehicle_type]
            self.max_res[5] = self.load_capacity[self.vehicle_type]

    def add_new_route(self, path):
        """Create new route as DiGraph and add to pool of columns"""
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        add_path(new_route, path)
        self.total_cost = 0
        for (i, j) in new_route.edges():
            edge_cost = self.sub_G.edges[i, j]["cost"][self.vehicle_type]
            self.total_cost += edge_cost
            new_route.edges[i, j]["cost"] = edge_cost
            if i != "Source":
                self.routes_with_node[i].append(new_route)
        new_route.graph["cost"] = self.total_cost
        new_route.graph["vehicle_type"] = self.vehicle_type
        self.routes.append(new_route)

    def add_max_stops(self):
        """Updates maximum number of stops."""
        # Change label
        self.resources[0] = "stops"
        # The Sink does not count (hence + 1)
        self.max_res[0] = self.num_stops + 1
        for (i, j) in self.sub_G.edges():
            self.sub_G.edges[i, j]["res_cost"][0] = 1

    def add_monotone(self):
        """Updates monotone resource."""
        # Change label
        self.resources[0] = "mono"
        for (i, j) in self.sub_G.edges():
            self.sub_G.edges[i, j]["res_cost"][0] = 1

    def add_max_load(self):
        """Updates maximum load."""
        self.max_res[1] = self.load_capacity[self.vehicle_type]
        for (i, j) in self.sub_G.edges():
            demand_head_node = self.sub_G.nodes[j]["demand"]
            self.sub_G.edges[i, j]["res_cost"][1] = demand_head_node

    def add_max_duration(self):
        """Updates maximum travel time."""
        self.max_res[2] = self.duration
        for (i, j) in self.sub_G.edges():
            travel_time = self.sub_G.edges[i, j]["time"]
            self.sub_G.edges[i, j]["res_cost"][2] = travel_time

    def get_REF(self):
        if self.time_windows or self.distribution_collection:
            # Use custom REF
            return _MyREFCallback(
                self.max_res,
                self.time_windows,
                self.distribution_collection,
                self.T,
                self.resources,
            )
        else:
            # Use default
            return None
