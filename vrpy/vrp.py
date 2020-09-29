import logging
from time import time
from pathlib import Path
from typing import List, Union

from networkx import DiGraph, shortest_path  # draw_networkx

from vrpy.greedy import _Greedy
from vrpy.master_solve_pulp import _MasterSolvePulp
from vrpy.subproblem_lp import _SubProblemLP
from vrpy.subproblem_cspy import _SubProblemCSPY
from vrpy.subproblem_greedy import _SubProblemGreedy
from vrpy.clarke_wright import _ClarkeWright, _RoundTrip
from vrpy.schedule import _Schedule
from vrpy.checks import (
    check_arguments,
    check_consistency,
    check_feasibility,
    check_initial_routes,
    check_vrp,
)
from vrpy.preprocessing import get_num_stops_upper_bound
from vrpy.hyper_heuristic import _HyperHeuristic
from csv import DictWriter

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
        load_capacity (list, optional):
            Maximum load per vehicle.
            Each item of the list points to a different capacity.
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
        fixed_cost (int, optional):
            Fixed cost per vehicle.
            Defaults to 0.
        num_vehicles (int, optional):
            Maximum number of vehicles available.
            Defaults to None (in this case num_vehicles is unbounded).
        periodic (int, optional):
            Time span if vertices are to be visited periodically.
            Defaults to None.
        mixed_fleet (bool, optional):
            True if heterogeneous fleet.
            Defaults to False.
        minimize_global_span (bool, optional):
            True if global span is minimized (instead of total cost).
            Defaults to False.
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
        periodic=None,
        mixed_fleet=False,
        minimize_global_span=False,
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
        self.num_vehicles = num_vehicles if num_vehicles is not None else []
        self.periodic = periodic
        self.mixed_fleet = mixed_fleet
        self.minimize_global_span = minimize_global_span

        # Solving parameters
        self.masterproblem: _MasterSolvePulp = None
        self.hyper_heuristic: _HyperHeuristic = None
        self.routes: List = []
        self.comp_time = None

        # Input solving parameters
        self._solver: str = None
        self._time_limit: int = None
        self._pricing_strategy: str = None
        self._exact: bool = None
        self._cspy: bool = None
        self._dive: bool = None
        self._greedy: bool = None
        self._max_iter: int = None
        self._run_exact = None  # iterations after which the exact algorithm is ran

        # parameters for column generation stopping criteria
        self._start_time = None
        self._more_routes = None
        self._iteration = 0  # current iteration
        self._no_improvement = 0  # iterations after with no change in obj func
        self._lower_bound = []
        # Parameters for initial solution and preprocessing
        self._max_capacity: int = None
        self._vehicle_types: Union[List, int] = None
        self._initial_routes = []
        self._preassignments = []
        self._dropped_nodes = []
        # Parameters for final solution
        self._best_value = None
        self._best_routes = []
        self._best_routes_as_graphs = []
        self._schedule: _Schedule = None
        # Check if given inputs are consistent
        check_vrp(self.G)

    def solve(
        self,
        initial_routes=None,
        preassignments=None,
        pricing_strategy="BestEdges1",
        cspy=True,
        exact=True,
        time_limit=None,
        solver="cbc",
        dive=False,
        greedy=False,
        max_iter=None,
        run_exact=1,
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
                Options available :
                    - "Exact": the subproblem is solved exactly;
                    - "BestEdges1": some edges are removed;
                    - "BestEdges2": some edges are removed (with a different strategy);
                    - "BestPaths": some edges are removed (with a different strategy);
                    - "Hyper": choose from the above using a hyper_heuristic (see hyper_heuristic.py);
                Defaults to "BestEdges1".
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
                Additionally, "gurobi" requires pulp to be installed from source.
                Defaults to "cbc", available by default.
            dive (bool, optional):
                True if diving heuristic is used.
                Defaults to False.
            greedy (bool, optional):
                True if randomized greedy algorithm is used to generate extra columns.
                Only valid for capacity constraints, time constraints, num stops constraints.
                Defaults to False.
            max_iter (int, optional):
                maximum number of iterations for the column generation procedure.
            run_exact (int, optional):
                if a pricing strategy is selected, this parameter controls the number of
                iterations after which the exact algorithm is run.
                Defaults to 1.

        Returns:
            float: Optimal solution of MIP based on generated columns
        """
        # set solving attributes
        self._more_routes = True
        self._solver = solver
        self._time_limit = time_limit
        self._pricing_strategy = pricing_strategy
        self._exact = exact
        self._cspy = cspy
        self._dive = False
        self._greedy = greedy
        self._max_iter = max_iter
        self._run_exact = run_exact
        if self._pricing_strategy == "Hyper":
            self.hyper_heuristic = _HyperHeuristic()

        self._start_time = time()
        if preassignments:
            self._preassignments = preassignments
        if initial_routes:
            self._initial_routes = initial_routes
        # If only one type of vehicle, some formatting is done
        if not self.mixed_fleet:
            self._format()
        # Pre-processing
        self._pre_solve()
        # Initialization
        self._initialize(solver)
        self._solve(dive, solver)

    @property
    def best_routes_type(self):
        return self._best_routes_vehicle_type

    @property
    def best_value(self):
        """Returns value of best solution found."""
        if self.drop_penalty:
            penalty = self.drop_penalty * len(self._dropped_nodes)
            if self.minimize_global_span:
                return max(self.best_routes_cost.values()) + penalty
            return sum(self.best_routes_cost.values()) + penalty
        if self.minimize_global_span:
            return max(self.best_routes_cost.values())
        return sum(self.best_routes_cost.values())

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
            edges = list(
                zip(self.best_routes[route][:-1], self.best_routes[route][1:]))
            k = self._best_routes_vehicle_type[route]
            cost[route] = sum(
                self._H.edges[i, j]["cost"][k] for (i, j) in edges)
        return cost

    @property
    def best_routes_load(self):
        """Returns dict with route ids as keys and route loads as values."""
        load = {}
        if (not self.load_capacity or self.distribution_collection or
                self.pickup_delivery):
            return load
        for route in self.best_routes:
            load[route] = sum(
                self._H.nodes[v]["demand"] for v in self.best_routes[route])
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
        if (not self.load_capacity and not self.pickup_delivery and
                not self.distribution_collection):
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
            edges = list(
                zip(self.best_routes[route][:-1], self.best_routes[route][1:]))
            # Travel times
            duration[route] = sum(
                self._H.edges[i, j]["time"] for (i, j) in edges)
            # Service times
            duration[route] += sum(self._H.nodes[v]["service_time"]
                                   for v in self.best_routes[route])

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
            arrival[i]["Source"] = self._H.nodes["Source"]["lower"]
            route = self.best_routes[i]
            for j in range(1, len(route)):
                tail = route[j - 1]
                head = route[j]
                arrival[i][head] = max(
                    arrival[i][tail] + self._H.nodes[tail]["service_time"] +
                    self._H.edges[tail, head]["time"],
                    self._H.nodes[head]["lower"],
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
            departure[i]["Source"] = self._H.nodes["Source"]["lower"]
            route = self.best_routes[i]
            for j in range(1, len(route) - 1):
                tail = route[j - 1]
                head = route[j]
                departure[i][head] = (max(
                    departure[i][tail] + self._H.nodes[tail]["service_time"] +
                    self._H.edges[tail, head]["time"],
                    self._H.nodes[head]["lower"],
                ) + self._H.nodes[head]["service_time"])
        return departure

    @property
    def schedule(self):
        """If Periodic CVRP, returns a dict with keys a day number and values
        the route IDs scheduled this day."""
        if self.periodic:
            return self._schedule
        return

    def _pre_solve(self):
        """Some pre-processing."""
        if self.mixed_fleet:
            self._define_vehicle_types()
        else:
            self._vehicle_types = 1
        # TODO collect all checks into a wrapper
        # Consistency , dive=Truechecks
        check_arguments(
            num_stops=self.num_stops,
            load_capacity=self.load_capacity,
            duration=self.duration,
            pricing_strategy=self._pricing_strategy,
            mixed_fleet=self.mixed_fleet,
            fixed_cost=self.fixed_cost,
            G=self.G,
            vehicle_types=self._vehicle_types,
            num_vehicles=self.num_vehicles,
        )
        # Setup fixed costs
        if self.fixed_cost:
            self._add_fixed_costs()
        # Setup default attributes if missing
        self._update_dummy_attributes()
        # Check options consistency
        check_consistency(
            cspy=self._cspy,
            pickup_delivery=self.pickup_delivery,
            pricing_strategy=self._pricing_strategy,
            G=self.G,
        )
        # Check feasibility
        check_feasibility(load_capacity=self.load_capacity,
                          G=self.G,
                          duration=self.duration)
        # Lock preassigned routes
        if self._preassignments:
            self._lock()
        # Remove infeasible arcs
        self._prune_graph()
        # Compute upper bound on number of stops as knapsack problem
        if self.load_capacity and not self.pickup_delivery:
            num_stops = get_num_stops_upper_bound(self.G, self._max_capacity,
                                                  self.num_stops,
                                                  self.distribution_collection)
            self.num_stops = num_stops
            logger.info("new upper bound : max num stops = %s" % num_stops)

    def _initialize(self, solver):
        """Initialization with feasible solution."""
        if self._initial_routes:
            # Initial solution is given as input
            check_initial_routes(initial_routes=self._initial_routes, G=self.G)
        else:
            # Initial solution is computed with Clarke & Wright (or round trips)
            self._get_initial_solution()
        # Initial routes are converted to digraphs
        self._convert_initial_routes_to_digraphs()
        # Init master problem
        self.masterproblem = _MasterSolvePulp(
            self.G,
            self._routes_with_node,
            self._routes,
            self.drop_penalty,
            self.num_vehicles,
            self.periodic,
            self.minimize_global_span,
            solver,
        )

    def _solve(self, dive, solver):
        self._column_generation()
        if dive:
            self._dive = True
            self._more_routes = True
            self._column_generation()
            (
                self._best_value,
                self._best_routes_as_graphs,
            ) = self.masterproblem.get_total_cost_and_routes(relax=True)
        elif len(self.G.nodes()) > 2:
            # Solve as MIP
            _, _ = self.masterproblem.solve(
                relax=False, time_limit=self._get_time_remaining(mip=True))
            (
                self._best_value,
                self._best_routes_as_graphs,
            ) = self.masterproblem.get_total_cost_and_routes(relax=False)
        self._post_process(solver)

    def _column_generation(self):
        while self._more_routes:
            # Generate good columns
            self._find_columns()
            # Stop if time limit is passed
            if (isinstance(self._get_time_remaining(), float) and
                    self._get_time_remaining() == 0.0):
                logger.info("time up !")
                break
            # Stop if no improvement limit is passed or max iter exceeded
            if self._no_improvement > 1000 or (
                    self._max_iter and self._iteration >= self._max_iter):
                break

    def _find_columns(self):
        "Solves masterproblem and pricing problem."
        # Solve restricted relaxed master problem
        if self._dive:
            duals, relaxed_cost = self.masterproblem.solve_and_dive(
                time_limit=self._get_time_remaining())
            if self.hyper_heuristic:
                self.hyper_heuristic.init(relaxed_cost)
        else:
            duals, relaxed_cost = self.masterproblem.solve(
                relax=True, time_limit=self._get_time_remaining())
        logger.info("iteration %s, %.6s" % (self._iteration, relaxed_cost))
        pricing_strategy = self._get_next_pricing_strategy(relaxed_cost)

        # One subproblem per vehicle type
        for vehicle in range(self._vehicle_types):
            # Solve pricing problem with randomised greedy algorithm
            if (self._greedy and not self.time_windows and
                    not self.distribution_collection and
                    not self.pickup_delivery and not self.minimize_global_span):
                subproblem = self._def_subproblem(duals, vehicle, greedy=True)
                self.routes, self._more_routes = subproblem.solve(n_runs=20)
                # Add initial_routes
                if self._more_routes:
                    for r in (r for r in self.routes
                              if r.graph["name"] not in self.masterproblem.y):
                        self.masterproblem.update(r)

            # Continue searching for columns
            self._more_routes = False
            if not self.minimize_global_span:
                self._more_routes = self._solve_subproblem_with_heuristic(
                    pricing_strategy=pricing_strategy,
                    vehicle=vehicle,
                    duals=duals)
            else:
                for route in self._routes[:len(self._routes)]:
                    self._more_routes = self._solve_subproblem_with_heuristic(
                        pricing_strategy=pricing_strategy,
                        vehicle=vehicle,
                        duals=duals,
                        route=route,
                    )
                    if self._more_routes:
                        break
            if self._more_routes:
                self.routes[-1].graph["heuristic"] = pricing_strategy
                self.masterproblem.update(self.routes[-1])
                break
            elif self._pricing_strategy == "Hyper":
                self.hyper_heuristic.end_time = time()

        # Keep track of convergence rate and update stopping criteria parameters
        self._iteration += 1
        if self._iteration > 1 and relaxed_cost == self._lower_bound[-1]:
            self._no_improvement += 1
        else:
            self._no_improvement = 0
            self._no_improvement_iteration = self._iteration
        if not self._dive:
            self._lower_bound.append(relaxed_cost)

    def _solve_subproblem_with_heuristic(
        self,
        pricing_strategy=None,
        vehicle=None,
        duals=None,
        route=None,
    ):
        """Solves pricing problem with input heuristic
        """
        more_columns = False
        if self._pricing_strategy == "Hyper":
            if pricing_strategy == "BestPaths":
                more_columns = self._attempt_solve_best_paths(vehicle=vehicle,
                                                              duals=duals,
                                                              route=route)
            elif pricing_strategy == "BestEdges1":
                more_columns = self._attempt_solve_best_edges1(vehicle=vehicle,
                                                               duals=duals,
                                                               route=route)
            elif pricing_strategy == "BestEdges2":
                more_columns = self._attempt_solve_best_edges2(vehicle=vehicle,
                                                               duals=duals,
                                                               route=route)
            elif pricing_strategy == "Exact":
                more_columns = self._attempt_solve_exact(vehicle=vehicle,
                                                         duals=duals,
                                                         route=route)
        # old approach
        else:
            if pricing_strategy == "BestPaths":
                more_columns = self._attempt_solve_best_paths(vehicle=vehicle,
                                                              duals=duals,
                                                              route=route)
            elif pricing_strategy == "BestEdges1":
                more_columns = self._attempt_solve_best_edges1(vehicle=vehicle,
                                                               duals=duals,
                                                               route=route)
            elif pricing_strategy == "BestEdges2":
                more_columns = self._attempt_solve_best_edges2(vehicle=vehicle,
                                                               duals=duals,
                                                               route=route)
            if pricing_strategy == "Exact" or not more_columns:
                more_columns = self._attempt_solve_exact(vehicle=vehicle,
                                                         duals=duals,
                                                         route=route)
        return more_columns

    def _attempt_solve_best_paths(self, vehicle=None, duals=None, route=None):
        more_columns = False
        for k_shortest_paths in [3, 5, 7, 9]:
            subproblem = self._def_subproblem(
                duals,
                vehicle,
                route,
                "BestPaths",
                k_shortest_paths,
            )
            self.routes, self._more_routes = subproblem.solve(
                self._get_time_remaining())
            more_columns = self._more_routes
            if more_columns:
                break
        else:
            self._more_routes = True
        return more_columns

    def _attempt_solve_best_edges1(self, vehicle=None, duals=None, route=None):
        more_columns = False
        for alpha in [0.3, 0.5, 0.7, 0.9]:
            subproblem = self._def_subproblem(
                duals,
                vehicle,
                route,
                "BestEdges1",
                alpha,
            )
            self.routes, self._more_routes = subproblem.solve(
                self._get_time_remaining(),)
            more_columns = self._more_routes
            if more_columns:
                break
        else:
            self._more_routes = True
        return more_columns

    def _attempt_solve_best_edges2(self, vehicle=None, duals=None, route=None):
        more_columns = False
        for ratio in [0.1, 0.2, 0.3]:
            subproblem = self._def_subproblem(
                duals,
                vehicle,
                route,
                "BestEdges2",
                ratio,
            )
            self.routes, self._more_routes = subproblem.solve(
                self._get_time_remaining(),
                # exact=False,
            )
            more_columns = self._more_routes
            if more_columns:
                break
        else:
            self._more_routes = True

        return more_columns

    def _attempt_solve_exact(self, vehicle=None, duals=None, route=None):
        subproblem = self._def_subproblem(duals, vehicle, route)
        self.routes, self._more_routes = subproblem.solve(
            self._get_time_remaining())
        return self._more_routes

    def _get_next_pricing_strategy(self, relaxed_cost):
        "Return the appropriate pricing strategy based on input parameters"
        pricing_strategy = None
        if (self._pricing_strategy == "Hyper" and
                self._no_improvement != self._run_exact):
            self._no_improvement_iteration = self._iteration
            if self._iteration == 0:
                pricing_strategy = "BestPaths"
                self.hyper_heuristic.init(relaxed_cost)
            else:
                # Get the active paths and the frequency list per heuristic
                self._update_hyper_heuristic(relaxed_cost)
                pricing_strategy = self.hyper_heuristic.pick_heuristic()
        elif self._no_improvement == self._run_exact:
            self._no_improvement = 0
            pricing_strategy = "Exact"
        else:
            pricing_strategy = self._pricing_strategy
        return pricing_strategy

    def _update_hyper_heuristic(self, relaxed_cost: float):
        best_paths, best_paths_freq = self.masterproblem.get_heuristic_distribution(
        )
        self.hyper_heuristic.current_performance(
            new_objective_value=relaxed_cost,
            produced_column=self._more_routes,
            active_columns=best_paths_freq)
        self.hyper_heuristic.move_acceptance()
        self.hyper_heuristic.update_parameters(self._iteration,
                                               self._no_improvement,
                                               self._no_improvement_iteration)

    def _get_time_remaining(self, mip: bool = False):
        """
        Modified to avoid over time in subproblems.

        Returns:
            - None if no time limit set.
            - time remaining (in seconds) if time remaining > 0 and mip = False
            - 5 if time remaining < 5 and mip = True
            - 0 if time remaining < 0
        """
        if self._time_limit:
            remaining_time = self._time_limit - (time() - self._start_time)
            if mip:
                return max(5, remaining_time)
            if remaining_time > 0:
                return remaining_time
            return 0.0
        return None

    def _def_subproblem(
        self,
        duals,
        vehicle_type,
        route=None,
        pricing_strategy="Exact",
        pricing_parameter=None,
        greedy=False,
    ):
        """Instanciates the subproblem."""

        if greedy:
            subproblem = _SubProblemGreedy(
                self.G,
                duals,
                self._routes_with_node,
                self._routes,
                vehicle_type,
                route,
                self.num_stops,
                self.load_capacity,
                self.duration,
                self.time_windows,
                self.pickup_delivery,
                self.distribution_collection,
            )
            return subproblem

        if self._cspy:
            # With cspy
            subproblem = _SubProblemCSPY(
                self.G,
                duals,
                self._routes_with_node,
                self._routes,
                vehicle_type,
                route,
                self.num_stops,
                self.load_capacity,
                self.duration,
                self.time_windows,
                self.pickup_delivery,
                self.distribution_collection,
                pricing_strategy,
                pricing_parameter,
                exact=self._exact,
            )
        else:
            # As LP
            subproblem = _SubProblemLP(
                self.G,
                duals,
                self._routes_with_node,
                self._routes,
                vehicle_type,
                route,
                self.num_stops,
                self.load_capacity,
                self.duration,
                self.time_windows,
                self.pickup_delivery,
                self.distribution_collection,
                pricing_strategy,
                pricing_parameter,
                solver=self._solver,
            )
        return subproblem

    # Preprocessing #

    def _get_initial_solution(self):
        """
        If no initial solution is given, creates one :
            - with Clarke & Wright if possible;
            - with a round trip otherwise.
        """
        self._initial_routes = []
        # Run Clarke & Wright if possible
        if (not self.time_windows and not self.pickup_delivery and
                not self.distribution_collection and not self.mixed_fleet and
                not self.periodic):
            best_value = 1e10
            best_num_vehicles = 1e10
            for alpha in [x / 10 for x in range(1, 20)]:
                # for beta in  [x / 10 for x in range(20)]:
                # for gamma in  [x / 10 for x in range(20)]:
                alg = _ClarkeWright(
                    self.G,
                    self.load_capacity,
                    self.duration,
                    self.num_stops,
                    alpha,
                    # beta,
                    # gamma,
                )
                alg.run()
                self._initial_routes += alg.best_routes
                if alg.best_value < best_value:
                    best_value = alg.best_value
                    best_num_vehicles = len(alg.best_routes)
            logger.info(
                "Clarke & Wright solution found with value %s and %s vehicles" %
                (best_value, best_num_vehicles))

            # Run greedy algorithm if possible
            alg = _Greedy(self.G, self.load_capacity, self.num_stops,
                          self.duration)
            alg.run()
            logger.info("Greedy solution found with value %s and %s vehicles" %
                        (alg.best_value, len(alg.best_routes)))
            self._initial_routes += alg.best_routes

        # If pickup and delivery, initial routes are Source-pickup-delivery-Sink
        elif self.pickup_delivery:
            for v in self.G.nodes():
                if "request" in self.G.nodes[v]:
                    self._initial_routes.append(
                        ["Source", v, self.G.nodes[v]["request"], "Sink"])
        # Otherwise compute round trips
        else:
            alg = _RoundTrip(self.G)
            alg.run()
            self._initial_routes = alg.round_trips

    def _convert_initial_routes_to_digraphs(self):
        """
        Converts list of initial routes to list of Digraphs.
        By default, initial routes are computed with vehicle type 0 (the first one in the list).
        """
        self._routes = []
        self._routes_with_node = {}
        for route_id, r in enumerate(self._initial_routes, start=1):
            total_cost = 0
            G = DiGraph(name=route_id)
            edges = list(zip(r[:-1], r[1:]))
            for (i, j) in edges:
                edge_cost = self.G.edges[i, j]["cost"][0]
                G.add_edge(i, j, cost=edge_cost)
                total_cost += edge_cost
            G.graph["cost"] = total_cost
            G.graph["vehicle_type"] = 0
            self._routes.append(G)
            for v in r[1:-1]:
                if v in self._routes_with_node:
                    self._routes_with_node[v].append(G)
                else:
                    self._routes_with_node[v] = [G]

    def _lock(self):
        """
        Processes preassigned routes and edges.
        If the route is complete, it is removed from the vrp.
        If not, for all edges of the incomplete route, the cost is set to 0
        (to guarantee that the sequence will remain as is).
        """
        for route in self._preassignments:
            edges = list(zip(route[:-1], route[1:]))
            # If the route cannot be extended, remove it
            if route[0] == "Source" and route[-1] == "Sink":
                logger.info("locking %s" % route)
                self.G.remove_nodes_from(route[1:-1])
            # Otherwise, keep it and set the costs to 0
            else:
                for (i, j) in edges:
                    for k in range(self._vehicle_types):
                        self.G.edges[i, j]["cost"][k] = 0

        # If all vertices are locked, do not generate columns
        if len(self.G.nodes()) == 2:
            self._more_routes = False

    def _add_fixed_costs(self):
        """Adds fixed cost on each outgoing edge from Source."""
        for v in self.G.successors("Source"):
            for k in range(self._vehicle_types):
                self.G.edges["Source", v]["cost"][k] += self.fixed_cost[k]

    def _remove_infeasible_arcs_capacities(self):
        infeasible_arcs = []
        for (i, j) in self.G.edges():
            if (self.G.nodes[i]["demand"] + self.G.nodes[j]["demand"] >
                    self._max_capacity):
                infeasible_arcs.append((i, j))
        self.G.remove_edges_from(infeasible_arcs)

    def _remove_infeasible_arcs_time_windows(self):
        infeasible_arcs = []
        for (i, j) in self.G.edges():
            travel_time = self.G.edges[i, j]["time"]
            service_time = self.G.nodes[i]["service_time"]
            tail_inf_time_window = self.G.nodes[i]["lower"]
            head_sup_time_window = self.G.nodes[j]["upper"]
            if tail_inf_time_window + travel_time + service_time > head_sup_time_window:
                infeasible_arcs.append((i, j))
            # Strengthen time windows
            for v in self.G.nodes():
                if v not in ["Source", "Sink"]:
                    # earliest time is coming straight from depot
                    self.G.nodes[v]["lower"] = max(
                        self.G.nodes[v]["lower"],
                        self.G.nodes["Source"]["lower"] +
                        self.G.edges["Source", v]["time"],
                    )
                    # Latest time is going straight to depot
                    self.G.nodes[v]["upper"] = min(
                        self.G.nodes[v]["upper"],
                        self.G.nodes["Sink"]["upper"] -
                        self.G.edges[v, "Sink"]["time"],
                    )
        self.G.remove_edges_from(infeasible_arcs)

    def _prune_graph(self):
        """
        Preprocessing:
           - Removes useless edges from graph
           - Strengthens time windows
        """
        if isinstance(self.load_capacity, list):
            self._max_capacity = max(self.load_capacity)
        else:
            self._max_capacity = self.load_capacity
        # Remove infeasible arcs (capacities)
        if self.load_capacity:
            self._remove_infeasible_arcs_capacities()

        # Remove infeasible arcs (time windows)
        if self.time_windows:
            self._remove_infeasible_arcs_time_windows()

    def _set_zero_attributes(self):
        """ Sets attr = 0 if missing """

        for v in self.G.nodes():
            for attribute in [
                    "demand",
                    "collect",
                    "service_time",
                    "lower",
                    "upper",
            ]:
                if attribute not in self.G.nodes[v]:
                    self.G.nodes[v][attribute] = 0
            # Ignore demand at Source/Sink
            if v in ["Source", "Sink"] and self.G.nodes[v]["demand"] > 0:
                logger.warning("Demand %s at node %s is ignored." %
                               (self.G.nodes[v]["demand"], v))
                self.G.nodes[v]["demand"] = 0

            # Set frequency = 1 if missing
            for attribute in ["frequency"]:
                if attribute not in self.G.nodes[v]:
                    self.G.nodes[v][attribute] = 1

    def _set_time_to_zero_if_missing(self):
        """ Sets time = 0 if missing """
        for (i, j) in self.G.edges():
            for attribute in ["time"]:
                if attribute not in self.G.edges[i, j]:
                    self.G.edges[i, j][attribute] = 0

    def _readjust_sink_time_windows(self):
        """ Readjusts Sink time windows """

        if self.G.nodes["Sink"]["upper"] == 0:
            self.G.nodes["Sink"]["upper"] = max(
                self.G.nodes[u]["upper"] + self.G.nodes[u]["service_time"] +
                self.G.edges[u, "Sink"]["time"]
                for u in self.G.predecessors("Sink"))

    def _update_dummy_attributes(self):
        """Adds dummy attributes on nodes and edges if missing."""

        # Set attr = 0 if missing
        self._set_zero_attributes()

        # Add Source-Sink so that subproblem is always feasible
        if ("Source", "Sink") not in self.G.edges():
            self.G.add_edge("Source", "Sink", cost=[0] * self._vehicle_types)

        # Set time = 0 if missing
        self._set_time_to_zero_if_missing()

        # Readjust Sink time windows
        self._readjust_sink_time_windows()

        # Keep a (deep) copy of the graph
        self._H = self.G.to_directed()

    def _best_routes_as_node_lists(self):
        """Converts route as DiGraph to route as node list."""
        self._best_routes = {}
        self._best_routes_vehicle_type = {}
        route_id = 1
        for route in self._best_routes_as_graphs:
            node_list = shortest_path(route, "Source", "Sink")
            self._best_routes[route_id] = node_list
            self._best_routes_vehicle_type[route_id] = route.graph[
                "vehicle_type"]
            route_id += 1
        # Merge with preassigned complete routes
        for route in self._preassignments:
            if route[0] == "Source" and route[-1] == "Sink":
                self._best_routes[route_id] = route
                edges = list(zip(route[:-1], route[1:]))
                best_cost = 1e10
                for k in range(self._vehicle_types):
                    # If different vehicles, the cheapest feasible one is accounted for
                    cost = sum(
                        self._H.edges[i, j]["cost"][k] for (i, j) in edges)
                    load = sum(self._H.nodes[i]["demand"] for i in route)
                    if cost < best_cost:
                        if self.load_capacity:
                            if load <= self.load_capacity[k]:
                                best_cost = cost
                                self._best_routes_vehicle_type[route_id] = k
                        else:
                            best_cost = cost
                            self._best_routes_vehicle_type[route_id] = k
                route_id += 1

    def _format(self):
        """Attributes are stored as singletons."""
        for (i, j) in self.G.edges():
            if not isinstance(self.G.edges[i, j]["cost"], list):
                self.G.edges[i, j]["cost"] = [self.G.edges[i, j]["cost"]]
        if self.num_vehicles and not isinstance(self.num_vehicles, list):
            self.num_vehicles = [self.num_vehicles]
        if self.fixed_cost and not isinstance(self.fixed_cost, list):
            self.fixed_cost = [self.fixed_cost]
        if self.load_capacity and not isinstance(self.load_capacity, list):
            self.load_capacity = [self.load_capacity]

    def _define_vehicle_types(self):
        """
        The number of types of vehicle is the length of load_capacity
        or fixed_cost or num_vehicles.
        """
        if self.load_capacity:
            self._vehicle_types = len(self.load_capacity)
        elif self.fixed_cost:
            self._vehicle_types = len(self.fixed_cost)
        elif self.num_vehicles:
            self._vehicle_types = len(self.num_vehicles)

    # Post-processing #

    def _post_process(self, solver):
        # Get dropped nodes
        if self.drop_penalty:
            self._dropped_nodes = self.masterproblem.dropped_nodes
        # Convert best routes into lists of nodes
        self._best_routes_as_node_lists()
        # Schedule routes over time span if Periodic CVRP
        if self.periodic:
            schedule = _Schedule(
                self.G,
                self.periodic,
                self.best_routes,
                self.best_routes_type,
                self.num_vehicles,
                solver,
            )
            schedule.solve(self._get_time_remaining())
            self._schedule = schedule.routes_per_day
        self.comp_time = time() - self._start_time
