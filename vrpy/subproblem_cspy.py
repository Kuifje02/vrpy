import numpy as np
import logging
import sys

sys.path.append("../../cspy")
from cspy import BiDirectional
from subproblem import SubProblemBase
from networkx import DiGraph, add_path

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
        self.resources = [
            "mono",
            "stops",
            "load",
            "time",
            "time windows",
            "elementarity",
        ]
        # Set number of resources as attribute of graph
        self.G.graph["n_res"] = len(self.resources)
        # Default lower and upper bounds
        self.min_res = [0 for x in range(len(self.resources))]
        self.max_res = [
            len(self.G.edges()),
            len(self.G.nodes()),
            sum([self.G.nodes[v]["demand"] for v in self.G.nodes()]),
            sum([self.G.edges[u, v]["time"] for (u, v) in self.G.edges()]),
            1,
            1,
        ]
        # Initialize cspy edge attributes
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"]
            edge[2]["res_cost"] = np.array([1, 1, 0, 0, 0, 0])

    def solve(self):
        """Solves the subproblem with cspy."""
        self.formulate()
        logger.debug("resources")
        logger.debug(self.resources)
        logger.debug(self.min_res)
        logger.debug(self.max_res)
        self.bidirect = BiDirectional(
            self.G,
            self.max_res,
            self.min_res,
            direction="both",
            REF=self.REF,
        )
        self.bidirect.run()
        logger.debug("subproblem")
        logger.debug("cost = %s" % self.bidirect.total_cost)
        logger.debug("resources = %s" % self.bidirect.consumed_resources)
        if self.bidirect.total_cost < -(10**-5):
            more_routes = True
            self.add_new_route()
            logger.debug("new route %s" % self.bidirect.path)
            logger.debug("new route cost = %s" % self.total_cost)
            return self.routes, more_routes
        else:
            more_routes = False
            return self.routes, more_routes

    def formulate(self):
        """Updates max_res depending on which contraints are active."""
        # Update weight attribute with duals
        self.add_dual_cost()
        # Problem specific constraints
        if self.num_stops:
            self.add_max_stops()
        if self.load_capacity:
            self.add_max_load()
        if self.duration:
            self.add_max_duration()
        if self.time_windows:
            # if not self.duration:
            # update upper bound for duration
            self.max_res[3] = 1 + self.G.nodes["Sink"]["upper"]
            self.max_res[4] = 0

    def add_new_route(self):
        """Create new route as DiGraph and add to pool of columns"""
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        add_path(new_route, self.bidirect.path)
        self.total_cost = 0
        for (i, j) in new_route.edges():
            edge_cost = self.G.edges[i, j]["cost"]
            self.total_cost += edge_cost
            new_route.edges[i, j]["cost"] = edge_cost
        new_route.graph["cost"] = self.total_cost
        self.routes.append(new_route)

    def add_dual_cost(self):
        """Updates edge weight attribute with dual values."""
        for edge in self.G.edges(data=True):
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]

    def add_max_stops(self):
        """Updates maximum number of stops."""
        # The Sink does not count (hence + 1)
        self.max_res[1] = self.num_stops + 1

    def add_max_load(self):
        """Updates maximum load."""
        self.max_res[2] = self.load_capacity
        for (i, j) in self.G.edges():
            demand_head_node = self.G.nodes[j]["demand"]
            self.G.edges[i, j]["res_cost"][2] = demand_head_node

    def add_max_duration(self):
        """Updates maximum travel time."""
        self.max_res[3] = self.duration
        for (i, j) in self.G.edges():
            travel_time = self.G.edges[i, j]["time"]
            self.G.edges[i, j]["res_cost"][3] = travel_time

    def REF(self, cumulative_res, edge):
        """
        Resource extension function based on Righini and Salani's paper
        """
        new_res = np.array(cumulative_res)
        # extract data
        tail_node, head_node, edge_data = edge[0:3]
        # monotone resource
        new_res[0] += 1
        # stops
        new_res[1] += 1
        # load
        new_res[2] += edge_data["res_cost"][2]
        # time
        arrival_time = new_res[3] + edge_data["res_cost"][3]
        service_time = 0  # undefined for now
        inf_time_window = self.G.nodes[head_node]["lower"]
        sup_time_window = self.G.nodes[head_node]["upper"]
        new_res[3] = max(arrival_time + service_time, inf_time_window)
        # time-window feasibility resource
        if new_res[3] <= sup_time_window:
            new_res[4] = 0
        else:
            new_res[4] = 1
        # elementarity
        new_res[5] = 0  # not implemented yet
        print(new_res)
        return new_res
