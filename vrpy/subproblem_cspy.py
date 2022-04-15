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

    def __init__(
        self,
        max_res,
        time_windows,
        distribution_collection,
        T,
        resources,
    ):
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
        # Travel times
        travel_time_ij = self._sub_G.edges[i, j]["time"]
        # Time windows
        # Lower
        a_j = self._sub_G.nodes[j]["lower"]
        # Upper
        b_j = self._sub_G.nodes[j]["upper"]

        new_res[2] = max(new_res[2] + theta_i + travel_time_ij, a_j)

        # time-window feasibility resource
        if not self._time_windows or (new_res[2] <= b_j):
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
        # Travel times
        travel_time_ij = self._sub_G.edges[i, j]["time"]
        # Lower time windows
        a_j = self._sub_G.nodes[j]["lower"]
        # Upper time windows
        b_i = self._sub_G.nodes[i]["upper"]
        b_j = self._sub_G.nodes[j]["upper"]

        new_res[2] = max(new_res[2] + theta_j + travel_time_ij, self._T - b_i - theta_i)

        # time-window feasibility
        if not self._time_windows or (new_res[2] <= self._T - a_j - theta_j):
            new_res[3] = 0
        else:
            new_res[3] = 1

        if self._distribution_collection:
            # Delivery
            new_res[5] += new_res[5] + self._sub_G.nodes[i]["demand"]
            # Pick up
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

    def __init__(self, *args, elementary):
        """Initializes resources."""
        # Pass arguments to base
        super(_SubProblemCSPY, self).__init__(*args)
        self.elementary = elementary
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
        # Average length of a path
        self._avg_path_len = 1
        # Iteration counter
        self._iters = 1

    # @profile
    def solve(self, time_limit):
        """
        Solves the subproblem with cspy.
        Time limit is reduced by 0.5 seconds as a safety window.

        Resolves at most twice:
        1. using elementary = False,
        2. using elementary = True, and threshold, if a route has already been
        found previously.
        """
        if not self.run_subsolve:
            return self.routes, False

        self.formulate()
        logger.debug("resources = {}".format(self.resources))
        logger.debug("min res = {}".format(self.min_res))
        logger.debug("max res = {}".format(self.max_res))

        more_routes = False

        my_callback = self.get_REF()
        direction = (
            "forward"
            if (
                self.time_windows
                or self.pickup_delivery
                or self.distribution_collection
            )
            else "both"
        )
        # Run only twice: Once with `elementary=False` check if route already
        # exists.

        s = (
            [False, True]
            if (not self.distribution_collection and not self.elementary)
            else [True]
        )
        for elementary in s:
            if elementary:
                # Use threshold if non-elementary (safe-guard against large
                # instances)
                thr = self._avg_path_len * min(
                    self.G.edges[i, j]["weight"] for (i, j) in self.G.edges()
                )
            else:
                thr = None
            logger.debug(
                f"Solving subproblem using elementary={elementary}, threshold={thr}, direction={direction}"
            )
            alg = BiDirectional(
                self.sub_G,
                self.max_res,
                self.min_res,
                threshold=thr,
                direction=direction,
                time_limit=time_limit - 0.5 if time_limit else None,
                elementary=elementary,
                REF_callback=my_callback,
                # pickup_delivery_pairs=self.pickup_delivery_pairs,
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
                new_route = self.create_new_route(alg.path)
                logger.debug(alg.path)
                path_len = len(alg.path)
                if not any(
                    list(new_route.edges()) == list(r.edges()) for r in self.routes
                ):
                    more_routes = True
                    self.routes.append(new_route)
                    self.total_cost = new_route.graph["cost"]
                    logger.debug("reduced cost = %s", alg.total_cost)
                    logger.debug("real cost = %s", self.total_cost)
                    if path_len > 2:
                        self._avg_path_len += (
                            path_len - self._avg_path_len
                        ) / self._iters
                        self._iters += 1
                    break
                else:
                    logger.info("Route already found, finding elementary one")
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
        if self.pickup_delivery:
            self.max_res[6] = 0

    def create_new_route(self, path):
        """Create new route as DiGraph and add to pool of columns"""
        e = "elem" if len(set(path)) == len(path) else "non-elem"
        route_id = "{}_{}".format(len(self.routes) + 1, e)
        new_route = DiGraph(name=route_id, path=path)
        add_path(new_route, path)
        total_cost = 0
        for (i, j) in new_route.edges():
            edge_cost = self.sub_G.edges[i, j]["cost"][self.vehicle_type]
            total_cost += edge_cost
            new_route.edges[i, j]["cost"] = edge_cost
            if i != "Source":
                self.routes_with_node[i].append(new_route)
        new_route.graph["cost"] = total_cost
        new_route.graph["vehicle_type"] = self.vehicle_type
        return new_route

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
        if self.time_windows or self.distribution_collection or self.pickup_delivery:
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
