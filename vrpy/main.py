from networkx import DiGraph, shortest_path
import logging
from pandas import DataFrame
from time import time

from vrpy.master_solve_pulp import MasterSolvePulp
from vrpy.subproblem_lp import SubProblemLP
from vrpy.subproblem_cspy import SubProblemCSPY
from vrpy.clarke_wright import ClarkeWright, RoundTrip

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VehicleRoutingProblem:
    """
    Stores the underlying network of the VRP and parameters for solving with a column generation approach.

    Args:
        G (DiGraph): The underlying network.
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
        pickup_delivery (bool, optional):
            True if pickup and delivery constraints.
            Defaults to False.
        distribution_collection (bool, optional):
            True if distribution and collection are simultaneously enforced.
            Defaults to False.
        drop_penalty (int, optional):
            Value of penalty if node is dropped.
            Defaults to None.
    """

    def __init__(
        self,
        G,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
        pickup_delivery=False,
        distribution_collection=False,
        drop_penalty=None,
    ):
        self.G = G
        # VRP options/constraints
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows
        self.pickup_delivery = pickup_delivery
        self.distribution_collection = distribution_collection
        self.drop_penalty = drop_penalty
        self._preassignment_cost = 0
        self._initial_routes = []

        # Attributes to keep track of solution
        self._iteration = []
        self._lower_bound = []

        # Keep track of paths containing nodes
        self._routes = []
        self._routes_with_node = {}
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                self._routes_with_node[v] = []

    def solve(
        self,
        initial_routes=None,
        preassignments=[],
        pricing_strategy="Exact",
        cspy=True,
        exact=True,
        time_limit=None,
        solver="cbc",
    ):
        """Iteratively generates columns with negative reduced cost and solves as MIP.

        Args:
            initial_routes (list, optional):
                List of paths (list of nodes).
                Feasible solution for first iteration.
                Defaults to None.
            preassignments (list, optional):
                List of preassigned routes, where a route is a list of nodes.
                If the route contains Source and Sink nodes, it is locked, otherwise it may be extended.
                Defaults to an emtpy list.
            pricing_strategy (str, optional):
                Strategy used for solving the sub problem.
                Five options available :
                    1. "Exact": the subproblem is solved exactly;
                    2. "Stops": the subproblem is solved with a limited number of stops;
                    3. "PrunePaths": the subproblem is solved on a subgraph of G;
                    4. "PruneEdges": the subproblem is solved on a subgraph of G;
                Defaults to "Exact".
            cspy (bool, optional):
                True if cspy is used for subproblem.
                Defaults to True.
            exact (bool, optional):
                True if only cspy's exact algorithm is used to generate columns.
                Otherwise, heuristics will be used until they produce +ve
                reduced cost columns, after which the exact algorithm is used.
                Defaults to True.
            time_limit (int, optional):
                Maximum number of seconds allowed for solving (for finding columns).
                Defaults to None.
            solver (str, optional):
                Solver used.
                Three options available: "cbc", "cplex", "gurobi".
                Using "cplex" or "gurobi" requires installation. Not available by default.
                Defaults to "cbc", available by default.
        Returns:
            float: Optimal solution of MIP based on generated columns
        """
        # Pre-processing
        self._pre_solve(cspy, preassignments)

        # Initialization
        more_routes = True
        if initial_routes:
            self._initial_routes = initial_routes
        else:
            self._get_initial_solution()
        self._convert_initial_routes_to_digraphs()

        k = 0
        no_improvement = 0
        start = time()

        # Generate interesting columns
        while more_routes and k < 1000 and no_improvement < 1000:

            # Solve restricted relaxed master problem
            masterproblem = MasterSolvePulp(
                self.G,
                self._routes_with_node,
                self._routes,
                self.drop_penalty,
                relax=True,
            )
            duals, relaxed_cost = masterproblem.solve(solver, time_limit)
            logger.info("iteration %s, %s" % (k, relaxed_cost))

            # The pricing problem is solved with a heuristic strategy
            if pricing_strategy == "Stops":
                for stop in range(2, self.num_stops):
                    subproblem = self._def_subproblem(
                        duals, cspy, exact, solver, pricing_strategy, stop,
                    )
                    self.routes, more_routes = subproblem.solve(time_limit)
                    if more_routes:
                        break

            if pricing_strategy == "PrunePaths":
                for k_shortest_paths in [3, 5, 7, 9]:
                    subproblem = self._def_subproblem(
                        duals, cspy, exact, solver, pricing_strategy, k_shortest_paths,
                    )
                    self.routes, more_routes = subproblem.solve(time_limit)
                    if more_routes:
                        break

            if pricing_strategy == "PruneEdges":
                for alpha in [0.3, 0.5, 0.7, 0.9]:
                    subproblem = self._def_subproblem(
                        duals, cspy, exact, solver, pricing_strategy, alpha,
                    )
                    self.routes, more_routes = subproblem.solve(time_limit)
                    if more_routes:
                        break

            # If no column was found heuristically, solve subproblem exactly
            if not more_routes or pricing_strategy == "Exact":
                subproblem = self._def_subproblem(duals, cspy, exact, solver,)
                self.routes, more_routes = subproblem.solve(time_limit)

            # Keep track of convergence rate
            k += 1
            if k > 1 and relaxed_cost == self._lower_bound[-1]:
                no_improvement += 1
            else:
                no_improvement = 0
            self._iteration.append(k)
            self._lower_bound.append(relaxed_cost)

            # Stop if time limit is passed
            if time_limit:
                if time() - start > time_limit:
                    logger.info("time up !")
                    break

        # Solve as MIP
        logger.info("MIP solution")
        masterproblem_mip = MasterSolvePulp(
            self.G, self._routes_with_node, self._routes, self.drop_penalty, relax=False
        )
        self._best_value, self._best_routes_as_graphs = masterproblem_mip.solve(
            solver, time_limit
        )
        self._best_routes_as_node_lists(preassignments)

        # Export relaxed_cost = f(iteration) to Excel file
        # self.export_convergence_rate()

    def _pre_solve(self, cspy, preassignments):
        """Some pre-processing."""
        # Lock preassigned routes
        if preassignments:
            self._lock(preassignments)
        # Set default attributes
        self._add_default_service_time()
        # Remove infeasible arcs
        self._prune_graph()
        # Compute upper bound on number of stops as knapsack problem
        if self.load_capacity and not self.pickup_delivery:
            self._get_num_stops_upper_bound()
        # Setup attributes if cspy
        if cspy:
            self._update_attributes_for_cspy()
            self._check_options_consistency()

    def _def_subproblem(
        self,
        duals,
        cspy,
        exact,
        solver,
        pricing_strategy="Exact",
        pricing_parameter=None,
    ):
        """Instanciates the subproblem."""
        if cspy:
            # With cspy
            subproblem = SubProblemCSPY(
                self.G,
                duals,
                self._routes_with_node,
                self._routes,
                self.num_stops,
                self.load_capacity,
                self.duration,
                self.time_windows,
                self.pickup_delivery,
                self.distribution_collection,
                pricing_strategy,
                pricing_parameter,
                exact=exact,
            )
        else:
            # As LP
            subproblem = SubProblemLP(
                self.G,
                duals,
                self._routes_with_node,
                self._routes,
                self.num_stops,
                self.load_capacity,
                self.duration,
                self.time_windows,
                self.pickup_delivery,
                self.distribution_collection,
                pricing_strategy,
                pricing_parameter,
                solver=solver,
            )
        return subproblem

    def _prune_graph(self):
        """
        Preprocessing:
           - Removes useless edges from graph
           - Strengthens time windows
        """
        infeasible_arcs = []
        # Remove infeasible arcs (capacities)
        if self.load_capacity:
            for (i, j) in self.G.edges():
                if (
                    self.G.nodes[i]["demand"] + self.G.nodes[j]["demand"]
                    > self.load_capacity
                ):
                    infeasible_arcs.append((i, j))

        # Remove infeasible arcs (time windows)
        if self.time_windows:
            for (i, j) in self.G.edges():
                travel_time = self.G.edges[i, j]["time"]
                service_time = self.G.nodes[i]["service_time"]
                tail_inf_time_window = self.G.nodes[i]["lower"]
                head_sup_time_window = self.G.nodes[j]["upper"]
                if (
                    tail_inf_time_window + travel_time + service_time
                    > head_sup_time_window
                ):
                    infeasible_arcs.append((i, j))

            # Strengthen time windows
            for v in self.G.nodes():
                if v not in ["Source", "Sink"]:
                    # earliest time is coming straight from depot
                    self.G.nodes[v]["lower"] = max(
                        self.G.nodes[v]["lower"],
                        self.G.nodes["Source"]["lower"]
                        + self.G.edges["Source", v]["time"],
                    )
                    # Latest time is going straight to depot
                    self.G.nodes[v]["upper"] = min(
                        self.G.nodes[v]["upper"],
                        self.G.nodes["Sink"]["upper"] - self.G.edges[v, "Sink"]["time"],
                    )
        self.G.remove_edges_from(infeasible_arcs)

    def _get_initial_solution(self):
        """
        If no initial solution is given, creates one :
            - with Clarke & Wright if possible;
            - with a round trip otherwise.
        """
        # Run Clarke & Wright if possible
        if (
            not self.time_windows
            and not self.pickup_delivery
            and not self.distribution_collection
            and not self.drop_penalty
        ):
            alg = ClarkeWright(
                self.G, self.load_capacity, self.duration, self.num_stops
            )
            alg.run()
            logger.info("Initial solution found with value %s" % alg.best_value)
            self._initial_routes = alg.best_routes

        # If pickup and delivery initial routes are Source-pickup-delivery-Sink
        elif self.pickup_delivery:
            for v in self.G.nodes():
                if "request" in self.G.nodes[v]:
                    self._initial_routes.append(
                        ["Source", v, self.G.nodes[v]["request"], "Sink"]
                    )
        # Otherwise compute round trips
        else:
            alg = RoundTrip(self.G)
            alg.run()
            self._initial_routes = alg.round_trips

    def _convert_initial_routes_to_digraphs(self):
        """Converts list of initial routes to list of Digraphs."""
        route_id = 0
        self._routes = []
        for r in self._initial_routes:
            total_cost = 0
            route_id += 1
            G = DiGraph(name=route_id)
            edges = list(zip(r[:-1], r[1:]))
            for (i, j) in edges:
                edge_cost = self.G.edges[i, j]["cost"]
                G.add_edge(i, j, cost=edge_cost)
                total_cost += edge_cost
            G.graph["cost"] = total_cost
            self._routes.append(G)
            for v in r:
                self._routes_with_node[v] = [G]

    def _update_attributes_for_cspy(self):
        """Adds dummy attributes on nodes and edges if missing."""

        if not self.load_capacity:
            for v in self.G.nodes():
                if "demand" not in self.G.nodes[v]:
                    self.G.nodes[v]["demand"] = 0
        if not self.time_windows:
            for v in self.G.nodes():
                if "lower" not in self.G.nodes[v]:
                    self.G.nodes[v]["lower"] = 0
                if "upper" not in self.G.nodes[v]:
                    self.G.nodes[v]["upper"] = 0
                if "service_time" not in self.G.nodes[v]:
                    self.G.nodes[v]["service_time"] = 0
            for (i, j) in self.G.edges():
                if "time" not in self.G.edges[i, j]:
                    self.G.edges[i, j]["time"] = 0
        if not self.distribution_collection:
            for v in self.G.nodes():
                if "collect" not in self.G.nodes[v]:
                    self.G.nodes[v]["collect"] = 0

    def _check_options_consistency(self):
        """
        The following options need are not implemented yet with cspy:
            -pickup and delivery
        """
        if self.pickup_delivery:
            raise NotImplementedError

    def _add_default_service_time(self):
        """Adds dummy service time."""
        if self.duration or self.time_windows:
            for v in self.G.nodes():
                if "service_time" not in self.G.nodes[v]:
                    self.G.nodes[v]["service_time"] = 0

    def _get_num_stops_upper_bound(self):
        """
        Finds upper bound on number of stops, from here :
        https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118

        A knapsack problem is solved to maximize the number of
        visits, subject to capacity constraints.
        """

        def knapsack(weights, capacity):
            """
            Binary knapsack solver with identical profits of weight 1.
            Args:
                weights (list) : list of integers
                capacity (int) : maximum capacity
            Returns:
                (int) : maximum number of objects
            """
            n = len(weights)
            # sol : [items, remaining capacity]
            sol = [[0] * (capacity + 1) for i in range(n)]
            added = [[False] * (capacity + 1) for i in range(n)]
            for i in range(n):
                for j in range(capacity + 1):
                    if weights[i] > j:
                        sol[i][j] = sol[i - 1][j]
                    else:
                        sol_add = 1 + sol[i - 1][j - weights[i]]
                        if sol_add > sol[i - 1][j]:
                            sol[i][j] = sol_add
                            added[i][j] = True
                        else:
                            sol[i][j] = sol[i - 1][j]
            return sol[n - 1][capacity]

        # Maximize sum of vertices such that sum of demands respect capacity constraints
        demands = [int(self.G.nodes[v]["demand"]) for v in self.G.nodes()]
        # Solve the knapsack problem
        max_num_stops = knapsack(demands, self.load_capacity)
        # Update num_stops attribute
        if self.num_stops:
            self.num_stops = min(max_num_stops, self.num_stops)
        else:
            self.num_stops = max_num_stops
        logger.info("new upper bound : max num stops = %s" % self.num_stops)

    def _lock(self, preassignments):
        """Processes preassigned routes."""
        for route in preassignments:
            extend = True
            edges = list(zip(route[:-1], route[1:]))
            # If the route cannot be extended
            if route[0] == "Source" and route[-1] == "Sink":
                logger.info("locking %s" % route)
                # Compute route cost and remove it from the VRP
                self._preassignment_cost += sum(
                    [self.G.edges[i, j]["cost"] for (i, j) in edges]
                )
                self.G.remove_nodes_from(route[1:-1])
                extend = False
            # If the route is partial with Source
            elif route[0] == "Source":
                self._preassignment_cost += self.G.edges["Source", route[1]]["cost"]
                self.G.edges["Source", route[1]]["cost"] = 0
            # If the route is partial with Sink
            elif route[-1] == "Sink":
                self._preassignment_cost += self.G.edges[route[-2], "Sink"]["cost"]
                self.G.edges[route[-2], "Sink"]["cost"] = 0
            if extend:
                for (i, j) in edges:
                    if i != "Source" and j != "Sink":
                        self._preassignment_cost += self.G.edges[i, j]["cost"]
                        self.G.edges[i, j]["cost"] = 0

    def _best_routes_as_node_lists(self, preassignments):
        """Converts route as DiGraph to route as node list."""
        self._best_routes = []
        for route in self._best_routes_as_graphs:
            node_list = shortest_path(route, "Source", "Sink")
            self._best_routes.append(node_list)
        # Merge with preassigned complete routes
        for route in preassignments:
            if route[0] == "Source" and route[-1] == "Sink":
                self._best_routes.append(route)

    def _export_convergence_rate(self):
        """Exports evolution of lowerbound to excel file."""
        keys = ["k", "z"]
        values = [self._iteration, self._lower_bound]
        convergence = dict(zip(keys, values))
        df = DataFrame(convergence, columns=keys)
        df.to_excel("convergence.xls", index=False)

    @property
    def best_value(self):
        """Returns value of best solution found."""
        return self._best_value + self._preassignment_cost

    @property
    def best_routes(self):
        """Returns list of best routes found, where a route is a list of nodes."""
        return self._best_routes
