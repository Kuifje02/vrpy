from master_solve_pulp import master_solve
from subproblem_lp import SubProblemLP
from subproblem_cspy import SubProblemCSPY


def main(
    G,
    initial_routes,
    cspy=False,
    num_stops=None,
    load_capacity=None,
    duration=None,
    time_windows=False,
):
    """Iteratively generates columns with negative reduced cost and solves as MIP.

    Args:
        G (DiGraph): [description]
        initial_routes (list): List of Digraphs ; feasible solution for first iteration.
        cspy (bool, optional): True if cspy is used for subproblem. Defaults to False.
        num_stops (int, optional): Maximum number of stops. Defaults to None.
        load_capacity (int, optional): Maximum load per vehicle. Defaults to None.
        duration (int, optional): Maximum duration of route. Defaults to None.
        time_windows (bool, optional): True if time windows on vertices. Defaults to False.

    Returns:
        float: Optimal solution of MIP based on generated columns
    """

    # initialization
    more_routes = True
    routes = initial_routes
    k = 0
    # generate interesting columns
    while more_routes:
        k += 1
        print("")
        print("iteration", k)
        print("===========")
        # solve restricted relaxed master problem
        duals, relaxed_cost = master_solve(G, routes, relax=True)
        # solve sub problem
        if cspy:
            # with cspy
            subproblem = SubProblemCSPY(
                G, duals, routes, num_stops, load_capacity, duration, time_windows
            )
            routes, more_routes = subproblem.solve()
        else:
            # as LP
            subproblem = SubProblemLP(
                G, duals, routes, num_stops, load_capacity, duration, time_windows
            )
            routes, more_routes = subproblem.solve()

    # solve as MIP
    print("")
    print("solve as MIP")
    print("============")
    best_value = master_solve(G, routes, relax=False)

    return best_value
