from cspy import BiDirectional
from networkx import DiGraph, add_path
import numpy as np
from subproblem import SubProblemBase


class SubProblemCSPY(SubProblemBase):
    """
    Solves the sub problem for the column generation procedure with cspy; attemps
    to find routes with negative reduced cost.

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

    def solve(self):
        self.init()
        self.formulate()
        self.bidirect = BiDirectional(
            self.G,
            self.max_res,
            self.min_res,
            direction="both",
            preprocess=True,
            REF_forward=None,  # self.REF_forward,
            REF_backward=None,  # self.REF_backward,
        )
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
        if self.time_windows:
            if not self.duration:
                # time resource is needed for time windows
                self.add_max_duration()
                # update upper bound for duration
                self.max_res[-1] = 1e10  # this is probably not the right way
            self.add_time_windows()
        self.G.graph["n_res"] = self.n_res

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
        # Set lower and upper bounds of load resource
        self.max_res.append(self.load_capacity)
        self.min_res.append(0)
        for (i, j) in self.G.edges():
            edge_array = self.G.edges[i, j]["res_cost"]
            demand_head_node = self.G.nodes[j]["demand"]
            self.G.edges[i, j]["res_cost"] = np.append(edge_array, [demand_head_node])

    def add_max_duration(self):
        # Increase number of resources by one unit
        self.n_res += 1
        # Set lower and upper bounds of time resource
        self.max_res.append(self.duration)
        self.min_res.append(0)
        for (i, j) in self.G.edges():
            edge_array = self.G.edges[i, j]["res_cost"]
            travel_time = self.G.edges[i, j]["time"]
            self.G.edges[i, j]["res_cost"] = np.append(edge_array, [travel_time])

    def add_time_windows(self):
        # Increase number of resources by one unit
        self.n_res += 1
        # Set lower and upper bounds to 0 (feasibility resource)
        self.max_res.append(0)
        self.min_res.append(0)
        for (i, j) in self.G.edges():
            edge_array = self.G.edges[i, j]["res_cost"]
            self.G.edges[i, j]["res_cost"] = np.append(edge_array, [0])

    """
    def REF_forward(self, cumulative_res, edge):
        if self.time_windows:
            return self.REF_forward_time_windows(cumulative_res, edge)

    def REF_backward(self, cumulative_res, edge):
        if self.time_windows:
            return self.REF_backward_time_windows(cumulative_res, edge)
    """

    def REF_forward(self, cumulative_res, edge):
        """Resource extension function based on Righini and Salani's paper
        """
        # extract data
        new_res = np.array(cumulative_res)
        head_node, tail_node, edge_data = edge[0:3]

        # monotone resource
        new_res[0] += 1

        # other resources
        # need help !
        # not sure how to deal with the fact that new_res has variable length
        # as is depends on which constraints are activated

        # time resource
        # we assume that time is always the penultimate resource (rank[-2])
        # and that time window feasibility is last (rank[-1])
        arrival_time = cumulative_res[-2] + edge_data["time"]
        service_time = 0  # undefined for now
        inf_time_window = self.G.nodes[head_node]["lower"]
        new_res[-2] += max(arrival_time + service_time, inf_time_window)
        # time-window feasibility resource
        sup_time_window = self.G.nodes[head_node]["lower"]
        if new_res[-2] <= sup_time_window:
            new_res[-1] = 0
        else:
            new_res[-1] = 1
        return new_res

    def REF_backward(self, cumulative_res, edge):
        """Resource extension function based on Righini and Salani's paper
        """
        new_res = np.array(cumulative_res)
        head_node, tail_node, edge_data = edge[0:3]
        # monotone resource
        new_res[0] += 1
        # other resources
        # need help !

        # time resource
        # we assume that time is always the penultimate resource (rank[-2])
        # and that time window feasibility is last (rank[-1])
        arrival_time = cumulative_res[-2] + edge_data["time"]
        service_time = 0  # undefined for now
        inf_time_window = self.G.nodes[head_node]["lower"]
        sup_time_window = self.G.nodes[head_node]["lower"]
        max_feasible_arrival_time = max(
            [
                self.G.nodes[v]["upper"] + self.G.edges[v, "Sink"]["time"]
                for v in self.G.predecessors("Sink")
            ]
        )
        new_res[-2] += max(
            arrival_time + service_time,
            max_feasible_arrival_time - sup_time_window - service_time,
        )
        # time-window feasibility resource
        if new_res[-2] <= max_feasible_arrival_time - inf_time_window - service_time:
            new_res[-1] = 0
        else:
            new_res[-1] = 1
        return new_res
