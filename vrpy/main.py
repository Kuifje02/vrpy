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


"""
if __name__ == "__main__":
    import networkx as nx
    G = nx.DiGraph()
    for v in [1, 2, 3, 4, 5]:
        G.add_edge("Source", v, cost=10, time=20)
        G.add_edge(v, "Sink", cost=10, time=20)
        G.nodes[v]["demand"] = 5
        G.nodes[v]["upper"] = 100
        G.nodes[v]["lower"] = 0
    G.nodes["Sink"]["demand"] = 0
    G.nodes["Sink"]["lower"] = 0
    G.nodes["Sink"]["upper"] = 100
    G.nodes["Source"]["demand"] = 0
    G.nodes["Source"]["lower"] = 0
    G.nodes["Source"]["upper"] = 100
    G.add_edge(1, 2, cost=10, time=20)
    G.add_edge(2, 3, cost=10, time=20)
    G.add_edge(3, 4, cost=15, time=20)
    G.add_edge(4, 5, cost=10, time=25)
    # Create routes
    initial_routes = []
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            route = nx.DiGraph(name=v, cost=20)
            route.add_edge("Source", v, cost=10)
            route.add_edge(v, "Sink", cost=10)
            initial_routes.append(route)
    main(
        G,
        initial_routes,
        cspy=True,
        num_stops=3,
        load_capacity=None,
        duration=None,
        time_windows=False,
    )
"""
