from numpy import array, zeros
import logging
import sys
from networkx import DiGraph, add_path

sys.path.append("../../cspy")

from cspy import BiDirectional, Tabu, GreedyElim
from subproblem import SubProblemBase

logger = logging.getLogger(__name__)


class SubProblemCSPY(SubProblemBase):
    """
    Solves the sub problem for the column generation procedure with cspy; attemps
    to find routes with negative reduced cost.

    Inherits problem parameters from `SubproblemBase`
    """

    def __init__(self, *args):
        """Initializes resources."""
        # Pass arguments to base
        super(SubProblemCSPY, self).__init__(*args)
        # Resource names
        self.exact = False
        self.alg = None
        self.resources = [
            "stops/mono",
            "load",
            "time",
            "time windows",
        ]
        self.exact = False
        # Set number of resources as attribute of graph
        self.G.graph["n_res"] = len(self.resources)
        # Default lower and upper bounds
        self.min_res = [0 for x in range(len(self.resources))]
        # Add upper bounds for mono, stops, load and time, and time windows
        self.max_res = [
            len(self.G.nodes()),
            sum([self.G.nodes[v]["demand"] for v in self.G.nodes()]),
            sum([self.G.edges[u, v]["time"] for (u, v) in self.G.edges()]),
            1,
        ]
        # Initialize cspy edge attributes
        for edge in self.G.edges(data=True):
            edge[2]["res_cost"] = zeros(len(self.resources))

    def solve(self):
        """Solves the subproblem with cspy.

        Resolves until:
        1. heuristic algorithm gives a new route (column with -ve reduced cost);
        2. exact algorithm gives a new route;
        3. neither heuristic nor exact give a new route.
        """
        self.formulate()
        logger.debug("resources = {}".format(self.resources))
        logger.debug("min res = {}".format(self.min_res))
        logger.debug("max res = {}".format(self.max_res))

        more_routes = False
        exact = False

        while True:
            if exact:
                logger.debug("solving with bidirectional")
                self.alg = BiDirectional(self.G,
                                         self.max_res,
                                         self.min_res,
                                         direction="both",
                                         REF=self.REF,
                                         method="generated")
            else:
                logger.debug("solving with greedyelim")
                self.alg = GreedyElim(self.G,
                                      self.max_res,
                                      self.min_res,
                                      REF=self.REF,
                                      max_depth=100)
            self.alg.run()
            logger.debug("subproblem")
            logger.debug("cost = %s" % self.alg.total_cost)
            logger.debug("resources = %s" % self.alg.consumed_resources)
            if self.alg.total_cost < -(10**-5):
                more_routes = True
                self.add_new_route()
                logger.debug("new route %s" % self.alg.path)
                logger.debug("new route cost = %s" % self.total_cost)
                break
            # If not already solved exactly
            elif not exact:
                exact = True
            # Solved heuristically and exactly and no more routes
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
            # if not self.duration:
            # update upper bound for duration
            self.max_res[2] = 1 + self.G.nodes["Sink"]["upper"]
            self.max_res[3] = 0

    def add_new_route(self):
        """Create new route as DiGraph and add to pool of columns"""
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        add_path(new_route, self.alg.path)
        self.total_cost = 0
        for (i, j) in new_route.edges():
            edge_cost = self.G.edges[i, j]["cost"]
            self.total_cost += edge_cost
            new_route.edges[i, j]["cost"] = edge_cost
        new_route.graph["cost"] = self.total_cost
        self.routes.append(new_route)

    def add_max_stops(self):
        """Updates maximum number of stops."""
        # Change label
        self.resources[0] = "stops"
        # The Sink does not count (hence + 1)
        self.max_res[0] = self.num_stops + 1
        for (i, j) in self.G.edges():
            self.G.edges[i, j]["res_cost"][0] = 1

    def add_monotone(self):
        """Updates monotone resource."""
        # Change label
        self.resources[0] = "mono"
        for (i, j) in self.G.edges():
            self.G.edges[i, j]["res_cost"][0] = 1

    def add_max_load(self):
        """Updates maximum load."""
        self.max_res[1] = self.load_capacity
        for (i, j) in self.G.edges():
            demand_head_node = self.G.nodes[j]["demand"]
            self.G.edges[i, j]["res_cost"][1] = demand_head_node

    def add_max_duration(self):
        """Updates maximum travel time."""
        self.max_res[2] = self.duration
        for (i, j) in self.G.edges():
            travel_time = self.G.edges[i, j]["time"]
            self.G.edges[i, j]["res_cost"][2] = travel_time

    def REF(self, cumulative_res, edge):
        """
        Resource extension function based on Righini and Salani's paper
        """
        new_res = array(cumulative_res)
        # extract data
        tail_node, head_node, edge_data = edge[0:3]
        # stops/monotone resource
        new_res[0] += 1
        # load
        new_res[1] += edge_data["res_cost"][1]
        # time
        arrival_time = new_res[2] + edge_data["res_cost"][2]
        service_time = 0
        # if "service_time" in self.G.nodes[head_node]:
        #     service_time = self.G.nodes[head_node]["service_time"]
        inf_time_window = self.G.nodes[head_node]["lower"]
        sup_time_window = self.G.nodes[head_node]["upper"]
        new_res[2] = max(arrival_time + service_time, inf_time_window)
        # time-window feasibility resource
        if new_res[2] <= sup_time_window:
            new_res[3] = 0
        else:
            new_res[3] = 1
        return new_res
