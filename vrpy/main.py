from networkx import DiGraph, shortest_path, NetworkXError, has_path
import logging
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
        fixed_cost (int: optional):
            Fixed cost per vehicle.
            Defaults to 0.
        num_vehicles (int: optional):
            Maximum number of vehicles available.
            Defaults to None (in this case num_vehicles is unbounded).
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
        fixed_cost=0,
        num_vehicles=None,
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
        self.fixed_cost = fixed_cost
        self.num_vehicles = num_vehicles
        self._preassignment_cost = 0
        self._initial_routes = []
        self._preassignments = []

        # Check if given inputs are consistent
        self._check_vrp()

        # Keep track of paths containing nodes
        self._routes = []
        self._routes_with_node = {}
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                self._routes_with_node[v] = []

    def solve(
        self,
        initial_routes=None,
        preassignments=None,
        pricing_strategy="Exact",
        cspy=True,
        exact=True,
        time_limit=None,
        solver="cbc",
    ):
        """Iteratively generates columns with negative reduced cost and solves as MIP.

        Args:
            initial_routes (list, optional):
                List of routes (ordered list of nodes).
                Feasible solution for first iteration.
                Defaults to None.
            preassignments (list, optional):
                List of preassigned routes (ordered list of nodes).
                If the route contains Source and Sink nodes, it is locked, otherwise it may be extended.
                Defaults to None.
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
        self._pre_solve(cspy, preassignments, pricing_strategy)

        # Initialization
        self._initialize(initial_routes)
        more_routes = True
        k = 0
        no_improvement = 0
        self._lower_bound = []
        start = time()

        # Generate interesting columns
        while more_routes and k < 1000 and no_improvement < 1000:
            more_routes, k, no_improvement = self._find_columns(
                k,
                more_routes,
                no_improvement,
                time_limit,
                pricing_strategy,
                cspy,
                exact,
                solver,
            )

            # Stop if time limit is passed
            if time_limit:
                if time() - start > time_limit:
                    logger.info("time up !")
                    break

        # Solve as MIP
        logger.info("MIP solution")
        masterproblem_mip = MasterSolvePulp(
            self.G,
            self._routes_with_node,
            self._routes,
            self.drop_penalty,
            self.num_vehicles,
            relax=False,
        )
        self._best_value, self._best_routes_as_graphs = masterproblem_mip.solve(
            solver, time_limit
        )
        # Convert best routes into lists of nodes
        self._best_routes_as_node_lists()

    def _pre_solve(self, cspy, preassignments, pricing_strategy):
        """Some pre-processing."""
        # Setup default attributes if missing
        self._update_dummy_attributes()
        # Check options consistency
        self._check_consistency(cspy, pricing_strategy)
        # Lock preassigned routes
        if preassignments:
            self._lock(preassignments)
        # Remove infeasible arcs
        self._prune_graph()
        # Compute upper bound on number of stops as knapsack problem
        if self.load_capacity and not self.pickup_delivery:
            self._get_num_stops_upper_bound()
        # Setup fixed costs
        if self.fixed_cost:
            self._add_fixed_costs()

    def _initialize(self, initial_routes):
        """Initialization with feasible solution."""
        if initial_routes:
            # Initial solution is given as input
            self._check(initial_routes)
            self._initial_routes = initial_routes
        else:
            # Initial solution is computed with Clarke & Wright (or round trips)
            self._get_initial_solution()
        # Initial routes are converted to digraphs
        self._convert_initial_routes_to_digraphs()

    def _find_columns(
        self,
        k,
        more_routes,
        no_improvement,
        time_limit,
        pricing_strategy,
        cspy,
        exact,
        solver,
    ):
        "Solves masterproblem and pricing problem."

        # Solve restricted relaxed master problem
        masterproblem = MasterSolvePulp(
            self.G,
            self._routes_with_node,
            self._routes,
            self.drop_penalty,
            self.num_vehicles,
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
        self._lower_bound.append(relaxed_cost)

        return more_routes, k, no_improvement

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

    def _add_fixed_costs(self):
        """Adds fixed cost on each outgoing edge from Source."""
        for v in self.G.successors("Source"):
            self.G.edges["Source", v]["cost"] += self.fixed_cost

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

    def _update_dummy_attributes(self):
        """Adds dummy attributes on nodes and edges if missing."""
        for v in self.G.nodes():
            for attribute in ["demand", "collect", "service_time", "lower", "upper"]:
                if attribute not in self.G.nodes[v]:
                    self.G.nodes[v][attribute] = 0
        if ("Source", "Sink") not in self.G.edges():
            self.G.add_edge("Source", "Sink", cost=0)
        for (i, j) in self.G.edges():
            for attribute in ["time"]:
                if attribute not in self.G.edges[i, j]:
                    self.G.edges[i, j][attribute] = 0
        # Keep a copy of the graph
        self._H = self.G.copy()

    def _check_vrp(self):
        """Checks if graph and vrp constraints are consistent."""
        # if G is not a DiGraph
        if not isinstance(self.G, DiGraph):
            raise TypeError(
                "Input graph must be of type networkx.classes.digraph.DiGraph."
            )
        for v in ["Source", "Sink"]:
            # If Source or Sink is missing
            if v not in self.G.nodes():
                raise KeyError("Input graph requires Source and Sink nodes.")
            # If Source has incoming edges
            if len(list(self.G.predecessors("Source"))) > 0:
                raise NetworkXError("Source must have no incoming edges.")
            # If Sink has outgoing edges
            if len(list(self.G.successors("Sink"))) > 0:
                raise NetworkXError("Sink must have no outgoing edges.")
        # If graph is disconnected
        if not has_path(self.G, "Source", "Sink"):
            raise NetworkXError("Source and Sink are not connected.")
        # If cost is missing
        for (i, j) in self.G.edges():
            if "cost" not in self.G.edges[i, j]:
                raise KeyError("Edge (%s,%s) requires cost attribute" % (i, j))
        # If num_stops/load_capacity/duration are not integers
        if self.num_stops is not None and (
            not isinstance(self.num_stops, int) or self.num_stops <= 0
        ):
            raise TypeError("Maximum number of stops must be positive integer.")
        if self.load_capacity is not None and (
            not isinstance(self.load_capacity, int) or self.load_capacity <= 0
        ):
            raise TypeError("Load capacity must be positive integer.")
        if self.duration is not None and (
            not isinstance(self.duration, int) or self.duration <= 0
        ):
            raise TypeError("Maximum duration must be positive integer.")

    def _check(self, initial_routes):
        """
        Checks if initial routes are consistent.
        TO DO : check if it is entirely feasible depending on VRP type.
        One way of doing it : run the subproblem by fixing variables corresponding to initial solution.
        """
        # Check if routes start at Sink and end at Node
        for route in initial_routes:
            if route[0] != "Source" or route[-1] != "Sink":
                raise ValueError(
                    "Route %s must start at Source and end at Sink" % route
                )
        # Check if every node is in exactly one route
        for v in self.G.nodes():
            if v not in ["Source", "Sink"]:
                node_found = 0
                for route in initial_routes:
                    if v in route:
                        node_found += 1
                if node_found == 0:
                    raise KeyError("Node %s missing from initial solution." % v)
                if node_found > 1:
                    raise ValueError(
                        "Node %s in more than one route in initial solution." % v
                    )
        # Check if edges from initial solution exist and have cost attribute
        for route in initial_routes:
            edges = list(zip(route[:-1], route[1:]))
            for (i, j) in edges:
                if (i, j) not in self.G.edges():
                    raise KeyError(
                        "Edge (%s,%s) in route %s missing in graph." % (i, j, route)
                    )
                if "cost" not in self.G.edges[i, j]:
                    raise KeyError("Edge (%s,%s) has no cost attribute." % (i, j))

    def _check_consistency(self, cspy, pricing_strategy):
        """Raises errors if options are inconsistent with parameters."""
        # pickup delivery requires cspy=False
        if cspy and self.pickup_delivery:
            raise NotImplementedError("pickup_delivery option requires cspy=False.")
        # pickup delivery requires pricing_stragy="Exact"
        if self.pickup_delivery and pricing_strategy != "Exact":
            raise ValueError(
                "pickup_delivery option requires 'Exact' pricing_strategy."
            )
        # pickup delivery expects at least one request
        if self.pickup_delivery:
            request = False
            for v in self.G.nodes():
                if "request" in self.G.nodes[v]:
                    request = True
                    break
            if not request:
                raise KeyError("pickup_delivery option expects at least one request.")

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
        if self.distribution_collection:
            collect = [int(self.G.nodes[v]["collect"]) for v in self.G.nodes()]
            max_num_stops = min(max_num_stops, knapsack(collect, self.load_capacity))
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
        self._preassignments = preassignments

    def _best_routes_as_node_lists(self):
        """Converts route as DiGraph to route as node list."""
        self._best_routes = {}
        route_id = 1
        for route in self._best_routes_as_graphs:
            node_list = shortest_path(route, "Source", "Sink")
            self._best_routes[route_id] = node_list
            route_id += 1
        # Merge with preassigned complete routes
        for route in self._preassignments:
            if route[0] == "Source" and route[-1] == "Sink":
                self._best_routes[route_id] = route
                route_id += 1

    @property
    def best_value(self):
        """Returns value of best solution found."""
        return self._best_value + self._preassignment_cost

    @property
    def best_routes(self):
        """
        Returns dict of best routes found.
        Keys : route_id; values : list of ordered nodes from Source to Sink."""
        return self._best_routes

    @property
    def best_routes_cost(self):
        """Returns dict with route ids as keys and route costs as values."""
        cost = {}
        for route in self.best_routes:
            edges = list(zip(self.best_routes[route][:-1], self.best_routes[route][1:]))
            cost[route] = (
                sum([self._H.edges[i, j]["cost"] for (i, j) in edges]) + self.fixed_cost
            )
        return cost

    @property
    def best_routes_load(self):
        """Returns dict with route ids as keys and route loads as values."""
        load = {}
        if not self.load_capacity:
            return load
        for route in self.best_routes:
            load[route] = sum(
                [self._H.nodes[v]["demand"] for v in self.best_routes[route]]
            )
        return load

    @property
    def node_load(self):
        """
        Returns nested dict.
        First key : route id ; second key : node ; value : load.
        If truck is collecting, load refers to accumulated load on truck.
        If truck is distributing, load refers to accumulated amount that has been unloaded.
        """
        load = {}
        if (
            not self.load_capacity
            and not self.pickup_delivery
            and not self.distribution_collection
        ):
            return load
        for i in self.best_routes:
            load[i] = {}
            amount = 0
            for v in self.best_routes[i]:
                amount += self._H.nodes[v]["demand"]
                if self.distribution_collection:
                    amount -= self._H.nodes[v]["collect"]
                load[i][v] = amount
            del load[i]["Source"]
        return load

    @property
    def best_routes_duration(self):
        """Returns dict with route ids as keys and route durations as values."""
        duration = {}
        if not self.duration and not self.time_windows:
            return duration
        for route in self.best_routes:
            edges = list(zip(self.best_routes[route][:-1], self.best_routes[route][1:]))
            # Travel times
            duration[route] = sum([self._H.edges[i, j]["time"] for (i, j) in edges])
            # Service times
            duration[route] += sum(
                [self._H.nodes[v]["service_time"] for v in self.best_routes[route]]
            )
        return duration

    @property
    def arrival_time(self):
        """
        Returns nested dict.
        First key : route id ; second key : node ; value : arrival time.
        """
        arrival = {}
        if not self.duration and not self.time_windows:
            return arrival
        for i in self.best_routes:
            arrival[i] = {}
            arrival[i]["Source"] = self.G.nodes["Source"]["lower"]
            route = self.best_routes[i]
            for j in range(1, len(route)):
                tail = route[j - 1]
                head = route[j]
                arrival[i][head] = max(
                    arrival[i][tail]
                    + self.G.nodes[tail]["service_time"]
                    + self.G.edges[tail, head]["time"],
                    self.G.nodes[head]["lower"],
                )
            del arrival[i]["Source"]
        return arrival

    @property
    def departure_time(self):
        """
        Returns nested dict.
        First key : route id ; second key : node ; value : departure time.
        """
        departure = {}
        if not self.duration and not self.time_windows:
            return departure
        for i in self.best_routes:
            departure[i] = {}
            departure[i]["Source"] = self.G.nodes["Source"]["lower"]
            route = self.best_routes[i]
            for j in range(1, len(route) - 1):
                tail = route[j - 1]
                head = route[j]
                departure[i][head] = (
                    max(
                        departure[i][tail]
                        + self.G.nodes[tail]["service_time"]
                        + self.G.edges[tail, head]["time"],
                        self.G.nodes[head]["lower"],
                    )
                    + self.G.nodes[head]["service_time"]
                )
        return departure
