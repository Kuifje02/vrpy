import networkx as nx
from master_solve_pulp import master_solve
# from sub_solve_pulp import sub_solve_lp
from subproblem_lp import SubProblemLP
from sub_solve_cspy import sub_solve_cspy


def main(
    G,
    initial_routes,
    cspy=False,
    num_stops=None,
    load_capacity=None,
    duration=None,
    time_windows=False,
):
    """Iteratively generates columns with negative reduced cost and solves as MIP
    
    Arguments:
        G {networkx DiGraph} 
        initial_routes {list of routes} -- Feasible solution for first iteration

    Keyword Arguments:
        cspy {bool} 
            True if cspy is used for solving subproblem
        num_stops {int} 
            Maximum number of stops. Optional. 
            If not provided, constraint not enforced.
        load_capacity {int} 
            Maximum capacity. Optional.
            If not provided, constraint not enforced.
        duration {int} 
            Maximum duration. Optional.
            If not provided, constraint not enforced.
        time_windows {bool} 
            True if time windows activated

    Returns:
        best_value -- Optimal solution of MIP based on generated columns
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
            routes, more_routes = sub_solve_cspy(G, duals, routes)
        else:
            # as LP
            subproblem = SubProblemLP(G, duals, routes, num_stops,
                                      load_capacity, duration, time_windows)
            routes, more_routes = subproblem.solve()

    # solve as MIP
    print("")
    print("solve as MIP")
    print("============")
    best_value = master_solve(G, routes, relax=False)

    return best_value


# if __name__ == "__main__":
#     G = create_graph()
#     initial_routes = initialize_routes(G)
#     main(
#         G,
#         initial_routes,
#         cspy=CSPY,
#         max_stop=MAX_STOP,
#         max_load=MAX_LOAD,
#         max_time=MAX_TIME,
#         time_windows=TIME_WINDOWS,
#     )
