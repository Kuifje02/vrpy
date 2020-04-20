from networkx import DiGraph
import logging
from pandas import DataFrame

from master_solve_pulp import MasterSolvePulp
from subproblem_lp import SubProblemLP
from subproblem_cspy import SubProblemCSPY

logger = logging.getLogger(__name__)


class VehicleRoutingProblem:
    """Stores the underlying network of the VRP and parameters for solving
       with a column generation approach.

    Args:
        G (DiGraph): The underlying network.
        initial_routes (list, optional):
            List of paths (list of nodes).
            Feasible solution for first iteration.
            Defaults to None.
        edge_cost_function (function, optional):
            Mapping with a cost for each edge.
            Only necessary if initial_routes is not None.
            Defaults to None.
        num_stops (int, optional):
            Maximum number of stops.
            Defaults to None.
        load_capacity (int, optional):
            Maximum load per vehicle.
            Defaults to None.
        duration (int, optional):
            Maximum duration of route.
            Defaults to None.
        time_windows (bool, optional):
            True if time windows on vertices.
            Defaults to False.
        undirected (bool, optional):
            True if underlying network is undirected.
            Defaults to True.
    """

    def __init__(
        self,
        G,
        initial_routes=None,
        edge_cost_function=None,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
        undirected=True,
    ):
        self.G = G
        self.initial_routes = initial_routes
        self.edge_cost_function = edge_cost_function
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows
        self.undirected = undirected

        # Remove infeasible arcs
        self.prune_graph()
        # Add index attribute for each node
        if self.undirected:
            self.create_index_for_nodes()

        # Attributes to keep track of solution
        self.best_solution = None
        self.best_routes = None
        self.iteration = []
        self.lower_bound = []

    # @profile
    def solve(self, cspy=True, exact=True):
        """Iteratively generates columns with negative reduced cost and solves as MIP.

        Args:
            cspy (bool, optional):
                True if cspy is used for subproblem.
                Defaults to True.
            exact (bool, optional):
                True if only cspy's exact algorithm is used to generate columns.
                Otherwise, heuristitics will be used until they produce +ve
                reduced cost columns, after which the exact algorithm is used.
                Defaults to True.
        Returns:
            float: Optimal solution of MIP based on generated columns
        """
        # Setup attributes if cspy
        if cspy:
            self.update_attributes_for_cspy()
        # Initialization
        more_routes = True
        if not self.initial_routes:
            self.initial_solution()
        else:
            self.initial_routes_to_digraphs()

        k = 0
        no_improvement = 0
        # generate interesting columns
        while more_routes and k < 1000 and no_improvement < 20:
            k += 1
            # solve restricted relaxed master problem
            masterproblem = MasterSolvePulp(self.G, self.routes, relax=True)
            duals, relaxed_cost = masterproblem.solve()
            logger.info("iteration %s, %s" % (k, relaxed_cost))
            self.iteration.append(k)
            if k > 1 and relaxed_cost == self.lower_bound[-1]:
                no_improvement += 1
            else:
                no_improvement = 0
            self.lower_bound.append(relaxed_cost)
            # solve sub problem
            if cspy:
                # with cspy
                subproblem = SubProblemCSPY(
                    self.G,
                    duals,
                    self.routes,
                    self.num_stops,
                    self.load_capacity,
                    self.duration,
                    self.time_windows,
                    self.undirected,
                    exact=exact,
                )
            else:
                # as LP
                subproblem = SubProblemLP(
                    self.G,
                    duals,
                    self.routes,
                    self.num_stops,
                    self.load_capacity,
                    self.duration,
                    self.time_windows,
                    self.undirected,
                )
            self.routes, more_routes = subproblem.solve()

        # export relaxed_cost = f(iteration) to Excel file
        # self.export_convergence_rate()
        # print(more_routes, k, no_improvement)

        # solve as MIP
        logger.info("MIP solution")
        masterproblem_mip = MasterSolvePulp(self.G, self.routes, relax=False)
        self.best_value, self.best_routes = masterproblem_mip.solve()

    def prune_graph(self):
        """Preprocessing:
           - Removes useless edges from graph
           - Strengthens time windows
        """
        infeasible_arcs = []
        # remove infeasible arcs (capacities)
        if self.load_capacity:
            for (i, j) in self.G.edges():
                if (self.G.nodes[i]["demand"] + self.G.nodes[j]["demand"] >
                        self.load_capacity):
                    infeasible_arcs.append((i, j))

        # remove infeasible arcs (time windows)
        if self.time_windows:
            for (i, j) in self.G.edges():
                travel_time = self.G.edges[i, j]["time"]
                service_time = 0  # for now
                tail_inf_time_window = self.G.nodes[i]["lower"]
                head_sup_time_window = self.G.nodes[j]["upper"]
                if (tail_inf_time_window + travel_time + service_time >
                        head_sup_time_window):
                    infeasible_arcs.append((i, j))

            # strenghten time windows
            for v in self.G.nodes():
                if v not in ["Source", "Sink"]:
                    # earliest time is coming straight from depot
                    self.G.nodes[v]["lower"] = max(
                        self.G.nodes[v]["lower"],
                        self.G.nodes["Source"]["lower"] +
                        self.G.edges["Source", v]["time"],
                    )
                    # latest time is going straight to depot
                    self.G.nodes[v]["upper"] = min(
                        self.G.nodes[v]["upper"],
                        self.G.nodes["Sink"]["upper"] -
                        self.G.edges[v, "Sink"]["time"],
                    )

        self.G.remove_edges_from(infeasible_arcs)

    def initial_solution(self):
        """If no initial solution is given, creates one"""
        initial_routes = []
        route_id = 0
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                route_id += 1
                if ("Source", v) in self.G.edges():
                    cost_1 = self.G.edges["Source", v]["cost"]
                else:
                    # if edge does not exist, create it with a high cost
                    cost_1 = 1e10
                    self.G.add_edge("Source", v, cost=cost_1)
                if (v, "Sink") in self.G.edges():
                    cost_2 = self.G.edges[v, "Sink"]["cost"]
                else:
                    # if edge does not exist, create it with a high cost
                    cost_2 = 1e10
                    self.G.add_edge(v, "Sink", cost=cost_2)
                total_cost = cost_1 + cost_2
                route = DiGraph(name=route_id, cost=total_cost)
                route.add_edge("Source", v, cost=cost_1)
                route.add_edge(v, "Sink", cost=cost_2)
                initial_routes.append(route)

        self.routes = initial_routes

    def initial_routes_to_digraphs(self):
        """Converts list of initial routes to list of Digraphs."""
        route_id = 0
        self.routes = []
        for r in self.initial_routes:
            total_cost = 0
            route_id += 1
            G = DiGraph(name=route_id)
            edges = list(zip(r[:-1], r[1:]))
            for (i, j) in edges:
                dist = round(self.edge_cost_function(i, j), 1)
                G.add_edge(i, j, cost=dist)
                total_cost += dist
            G.graph["cost"] = total_cost
            self.routes.append(G)

    def update_attributes_for_cspy(self):
        """Adds dummy attributes on nodes and edges if missing."""
        if not self.time_windows:
            for v in self.G.nodes():
                if "lower" not in self.G.nodes[v]:
                    self.G.nodes[v]["lower"] = 0
                if "upper" not in self.G.nodes[v]:
                    self.G.nodes[v]["upper"] = 0
            for (i, j) in self.G.edges():
                if "time" not in self.G.edges[i, j]:
                    self.G.edges[i, j]["time"] = 0

    def create_index_for_nodes(self):
        """An index is created for each node ;
           usefull if node names are not integers.
        """
        self.G.nodes["Source"]["id"] = 0
        self.G.nodes["Sink"]["id"] = len(self.G.nodes()) - 1
        index = 0
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                index += 1
                self.G.nodes[v]["id"] = index

    def export_convergence_rate(self):
        """Exports evolution of lowerbound to excel file.
        """
        keys = ["k", "z"]
        values = [self.iteration, self.lower_bound]
        convergence = dict(zip(keys, values))
        df = DataFrame(convergence, columns=keys)
        df.to_excel("convergence.xls", index=False)
