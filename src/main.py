import networkx as nx
from column_generation import master_solve, sub_solve_lp


def main(G):
    """Iteratively generates columns with negative reduced cost and solves as MIP
    
    Arguments:
        G {networkx DiGraph} 
    """
    # initialization
    more_routes = True
    routes = initialize_routes(G)
    route_id = len(routes)
    k = 0
    # generate interesting columns
    while more_routes and k < 4:
        k += 1
        print("")
        print("iteration", k)
        print("===========")
        # solve restricted relaxed master problem
        duals, relaxed_cost = master_solve(G, routes, relax=True)
        # solve sub problem
        routes, more_routes, route_id = sub_solve_lp(G, duals, routes, route_id)
        # routes, more_routes, route_id = sub_solve_cspy(G, duals, routes, route_id)

    # solve as MIP
    print("")
    print("solve as MIP")
    print("============")
    master_solve(G, routes, relax=False)

    return


def create_graph():
    """Creates a toy graph
    
    Returns:
        G -- A networkx DiGraph
    """
    G = nx.DiGraph()
    for v in [1, 2, 3, 4]:
        G.add_edge("Source", v, cost=10)
        G.add_edge(v, "Sink", cost=10)
    G.add_edge(1, 2, cost=10)
    G.add_edge(2, 3, cost=15)
    G.add_edge(3, 4, cost=10)
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
    routes = initialize_routes(G)
    main(G)
