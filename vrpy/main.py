from networkx import DiGraph

from master_solve_pulp import MasterSolvePulp
from subproblem_lp import SubProblemLP
from subproblem_cspy import SubProblemCSPY


class VRPSolver:
    """Stores the underlying network of the VRP and parameters for solving
       with a column generation approach.

    Args:
        G (DiGraph): The underlying network.
        initial_routes (list, optional):
            List of Digraphs.
            Feasible solution for first iteration.
            Defaults to None.
        cspy (bool, optional):
            True if cspy is used for subproblem.
            Defaults to False.
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
    """

    def __init__(
        self,
        G,
        initial_routes=None,
        cspy=False,
        num_stops=None,
        load_capacity=None,
        duration=None,
        time_windows=False,
    ):
        self.G = G
        self.initial_routes = initial_routes
        self.cspy = cspy
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows

    def column_generation(self):
        """Iteratively generates columns with negative reduced cost and solves as MIP.

        Returns:
            float: Optimal solution of MIP based on generated columns
        """

        # initialization
        more_routes = True
        if not self.initial_routes:
            self.initial_solution()
        else:
            self.routes = self.initial_routes
        k = 0
        # generate interesting columns
        while more_routes:
            k += 1
            print("")
            print("iteration", k)
            print("===========")
            # solve restricted relaxed master problem
            masterproblem = MasterSolvePulp(self.G, self.routes, relax=True)
            duals, relaxed_cost = masterproblem.solve()
            # solve sub problem
            if self.cspy:
                # with cspy
                subproblem = SubProblemCSPY(
                    self.G,
                    duals,
                    self.routes,
                    self.num_stops,
                    self.load_capacity,
                    self.duration,
                    self.time_windows,
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
                )
            self.routes, more_routes = subproblem.solve()

        # solve as MIP
        print("")
        print("solve as MIP")
        print("============")
        masterproblem_mip = MasterSolvePulp(self.G, self.routes, relax=False)
        best_value = masterproblem_mip.solve()

        return best_value

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
