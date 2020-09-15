from random import choice
from networkx import DiGraph, add_path

# from os import sys
# sys.path.append("../")
from .subproblem import _SubProblemBase
import logging

logger = logging.getLogger(__name__)


class _SubProblemGreedy(_SubProblemBase):
    """
    Solves the sub problem for the column generation procedure with
    a greedy randomised heuristic.
    Described here: https://www.sciencedirect.com/science/article/abs/pii/S0377221717306045

    Inherits problem parameters from `SubproblemBase`
    """

    def __init__(self, *args):
        # Pass arguments to base
        super(_SubProblemGreedy, self).__init__(*args)

    def _initialize_run(self):
        self._load = 0
        self._time = 0
        self._stops = 0
        self._weight = 0

    def solve(self, n_runs=5):
        """The forward and backwards search are run."""
        more_routes = False
        # The forward search is run n_runs times
        for _ in range(n_runs):
            self._initialize_run()
            self.run_forward()
            if self._new_node and self._weight < 0:
                logger.debug("negative column %s" % self._weight)
                more_routes = True
                self._add_new_route()
        # The backwards search is run n_runs times
        for _ in range(n_runs):
            self._initialize_run()
            self.run_backwards()
            if self._new_node and self._weight < 0:
                logger.debug("negative column %s" % self._weight)
                more_routes = True
                self._add_new_route()
        return self.routes, more_routes

    def run_forward(self):
        """
        A path starting from Source is randomly greedily extended
        until Sink is reached.
        The procedure aborts if path becomes infeasible.
        """
        self._current_path = ["Source"]
        extend = True
        new_node = True
        while extend and new_node:
            new_node = self._get_next_node()
            extend = self._update(forward=True)

    def _get_next_node(self):
        self._last_node = self._current_path[-1]
        out_going_costs = {}
        # Store the successors reduced cost that meet constraints
        for v in self.sub_G.successors(self._last_node):
            if self._constraints_met(v, forward=True):
                out_going_costs[v] = self.sub_G.edges[self._last_node, v]["weight"]
        if out_going_costs == {}:
            logger.debug("path cannot be extended")
            self._new_node = None
            return False
        else:
            # Randomly select a node among the 5 best ones
            pool = sorted(out_going_costs, key=out_going_costs.get)[:5]
            self._new_node = choice(pool)
            return True

    def _constraints_met(self, v, forward):
        """Checks if constraints are respected."""
        if v in self._current_path or self._check_source_sink(v):
            return False
        elif self.load_capacity and not self._check_capacity(v):
            return False
        elif self.duration and not self._check_duration(v, forward):
            return False
        else:
            return True

    def run_backwards(self):
        self._current_path = ["Sink"]
        extend = True
        new_node = True
        while extend and new_node:
            new_node = self._get_previous_node()
            extend = self._update(forward=False)

    def _get_previous_node(self):
        self._last_node = self._current_path[0]
        incoming_costs = {}
        # Store the reduced costs of the predecessors that meet constraints
        for v in self.sub_G.predecessors(self._last_node):
            if self._constraints_met(v, forward=False):
                incoming_costs[v] = self.sub_G.edges[v, self._last_node]["weight"]
        if not incoming_costs:
            logger.debug("path cannot be extended")
            self._new_node = None
            return False
        else:
            # Randomly select a node among the 5 best ones
            pool = sorted(incoming_costs, key=incoming_costs.get)[:5]
            self._new_node = choice(pool)
            return True

    def _update(self, forward):
        """Updates path, path load, path time, path weight."""
        if not self._new_node:
            return

        self._stops += 1
        self._load += self.sub_G.nodes[self._new_node]["demand"]
        if forward:
            self._weight += self.sub_G.edges[self._last_node, self._new_node]["weight"]
            self._time += self.sub_G.edges[self._last_node, self._new_node]["time"]
            self._current_path.append(self._new_node)
            if self._stops == self.num_stops and self._new_node != "Sink":
                # Finish path
                if self._new_node in self.sub_G.predecessors("Sink"):
                    self._current_path.append("Sink")
                else:
                    self._new_node = False
                return False
            elif self._new_node == "Sink":
                return False
        else:
            self._weight += self.sub_G.edges[self._new_node, self._last_node]["weight"]
            self._time += self.sub_G.edges[self._new_node, self._last_node]["time"]
            self._current_path.insert(0, self._new_node)
            if self._stops == self.num_stops and self._new_node != "Source":
                # Finish path
                if self._new_node in self.sub_G.successors("Sink"):
                    self._current_path.insert(0, "Source")
                else:
                    self._new_node = False
                return False
            elif self._new_node == "Source":
                return False
        return True

    def _add_new_route(self):
        """Create new route as DiGraph and add to pool of columns"""
        route_id = len(self.routes) + 1
        new_route = DiGraph(name=route_id)
        add_path(new_route, self._current_path)
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

    def _check_source_sink(self, v):
        """Checks if edge Source Sink."""
        return self._last_node == "Source" and v == "Sink"

    def _check_capacity(self, v):
        """Checks capacity constraint."""
        return (
            self._load + self.sub_G.nodes[v]["demand"]
            <= self.load_capacity[self.vehicle_type]
        )

    def _check_duration(self, v, forward):
        """Checks time constraint."""
        if forward:
            return (
                self._time + self.sub_G.edges[self._last_node, v]["time"]
                <= self.duration
            )
        else:
            return (
                self._time + self.sub_G.edges[v, self._last_node]["time"]
                <= self.duration
            )

    """
    NOT IMPLEMENTED YET
    def _check_time_windows(self, v, forward):
        #Checks time window feasibility
        if forward:
            return (
                self._time + self.sub_G.edges[self._last_node, v]["time"]
                <= self.sub_G.nodes[v]["upper"]
            )
        else:
            return (
                self._time + self.sub_G.edges[v, self._last_node]["time"]
                <= self.sub_G.nodes[v]["upper"]
            )
    """
