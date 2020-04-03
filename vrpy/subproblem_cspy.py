from cspy import BiDirectional
from networkx import DiGraph, add_path
import numpy as np
from subproblem import SubProblemBase


class SubProblemCSPY(SubProblemBase):
    """
    Solves the sub problem for the column generation procedure with cspy; attemps
    to find routes with negative reduced cost

    Inherits problem parameters from `SubproblemBase`
    """

    def init(self):
        # Initialize monotone resource
        self.n_res = 1
        self.min_res = [0]
        self.max_res = [len(self.G.edges())]
        # Initialize cspy edge attributes
        for edge in self.G.edges(data=True):
            edge[2]["weight"] = edge[2]["cost"]
            edge[2]["res_cost"] = np.array([1])
        # cspy BiDirectional algorithm
        self.bidirect = None

    def solve(self):
        self.init()
        self.formulate()
        self.bidirect.run()
        print("subproblem")
        print("cost =", self.bidirect.total_cost)
        print("resources =", self.bidirect.consumed_resources)
        if self.bidirect.total_cost < -(10 ** -5):
            more_routes = True
            self.add_new_route()
            print("new route", self.bidirect.path)
            print("new route cost =", self.total_cost)
            return self.routes, more_routes
        else:
            more_routes = False
            return self.routes, more_routes

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

    def formulate(self):
        # Update weight attribute with duals
        self.add_dual_cost()
        # Problem specific constraints
        if self.num_stops:
            self.add_max_stops()
        if self.load_capacity:
            self.add_max_load()
        if self.duration:
            self.add_max_duration()
        """
        if self.time_windows:
            self.add_time_windows()
        """
        self.G.graph["n_res"] = self.n_res
        print("n resources =", self.n_res)
        # print(self.edges(data=True))
        self.bidirect = BiDirectional(self.G, self.max_res, self.min_res)

    def add_dual_cost(self):
        """Updates edge weight attribute with dual values."""
        for edge in self.G.edges(data=True):
            for v in self.duals:
                if edge[0] == v:
                    edge[2]["weight"] -= self.duals[v]

    def add_max_stops(self):
        # Increase number of resources by one unit
        self.n_res += 1
        # Set lower and upper bounds of stop resource
        self.max_res.append(self.num_stops + 1)
        self.min_res.append(0)
        for edge in self.G.edges(data=True):
            edge_array = edge[2]["res_cost"]
            edge[2]["res_cost"] = np.append(edge_array, [1])

    def add_max_load(self):
        # Increase number of resources by one unit
        self.n_res += 1
        # Set lower and upper bounds of stop resource
        self.max_res.append(self.load_capacity)
        self.min_res.append(0)
        for (i, j) in self.G.edges():
            edge_array = self.G.edges[i, j]["res_cost"]
            demand = self.G.nodes[j]["demand"]
            self.G.edges[i, j]["res_cost"] = np.append(edge_array, [demand])

    def add_max_duration(self):
        # Increase number of resources by one unit
        self.n_res += 1
        # Set lower and upper bounds of stop resource
        self.max_res.append(self.duration)
        self.min_res.append(0)
        for (i, j) in self.G.edges():
            edge_array = self.G.edges[i, j]["res_cost"]
            travel_time = self.G.edges[i, j]["time"]
            self.G.edges[i, j]["res_cost"] = np.append(edge_array, [travel_time])

    """
    def add_time_windows(self):
    """
