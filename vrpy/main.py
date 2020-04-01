import networkx as nx
from master_solve_pulp import master_solve
from sub_solve_pulp import sub_solve_lp
from sub_solve_cspy import sub_solve_cspy

# Parameters
CSPY = False  # use cspy for subproblem, otherwise use LP
MAX_STOP = True  # max 3 stops per vehicle
MAX_LOAD = True  # max 10 units per vehicle
MAX_TIME = False  # max 60 minutes per vehicle
TIME_WINDOWS = True  # time window constraints on each node


def main(
    G,
    initial_routes,
    cspy=False,
    max_stop=True,
    max_load=False,
    max_time=False,
    time_windows=False,
):
    """Iteratively generates columns with negative reduced cost and solves as MIP
    
    Arguments:
        G {networkx DiGraph} 
        initial_routes {list of routes} -- Feasible solution for first iteration

    Keyword Arguments:
        cspy {bool} -- True if cspy is used for solving subproblem
        max_stop {bool} -- True if stop constraints activated
        max_load {bool} -- True if capacity constraints activated
        max_time {bool} -- True if time constraints activated 
        time_windows {bool} -- True if time windows activated

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
            routes, more_routes = sub_solve_lp(
                G, duals, routes, max_stop, max_load, max_time, time_windows
            )

    # solve as MIP
    print("")
    print("solve as MIP")
    print("============")
    best_value = master_solve(G, routes, relax=False)

    return best_value


def create_graph():
    """Creates a toy graph
    
    Returns:
        G -- A networkx DiGraph
    """
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
    return G


def initialize_routes(G):
    """Sets the initial routes for first iteration
    
    Arguments:
        G {networkx DiGraph} -- The graph representing the network
    
    Returns:
        routes -- A list of initial routes as network DiGraphs
    """
    routes = []
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            route = nx.DiGraph(name=v, cost=20)
            route.add_edge("Source", v, cost=10)
            route.add_edge(v, "Sink", cost=10)
            routes.append(route)
    return routes


if __name__ == "__main__":
    G = create_graph()
    initial_routes = initialize_routes(G)
    main(
        G,
        initial_routes,
        cspy=CSPY,
        max_stop=MAX_STOP,
        max_load=MAX_LOAD,
        max_time=MAX_TIME,
        time_windows=TIME_WINDOWS,
    )
