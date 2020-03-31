import networkx as nx
import numpy as np
import cspy


def add_cspy_edge_attributes(G):
    """
    Set edge attributes required for cspy
    """
    # Iterate through edges to specify 'weight' and 'res_cost' attributes
    G.graph["n_res"] = 2
    for edge in G.edges(data=True):
        # print(edge)
        edge[2]["weight"] = edge[2]["cost"]
        edge[2]["res_cost"] = np.array([1, 1])
    return G


def add_dual_cost(G, duals):
    """Updates edge weight attribute with dual values
    
    Arguments:
        G {networkx.digraph} 
        duals {dict} 
    
    Returns:
        G 
    """
    for edge in G.edges(data=True):
        for v in duals:
            if edge[0] == v:
                edge[2]["weight"] -= duals[v]
    return G


def sub_solve_cspy(G, duals, routes, route_id):
    """Solves subproblem with cspy bidirectional algorithm
    
    Arguments:
        G {networkx.DiGraph} -- Graph representing the network
        duals {dict} -- Dictionary of dual values of master problem
        routes {list} -- List of current routes/variables/columns
        route_id {int} -- Last route ID number used
    
    Returns:
        routes, more_routes, route_id -- updated routes, boolean as True if new route was found, route ID number of found route
    """
    G = add_cspy_edge_attributes(G)
    G = add_dual_cost(G, duals)
    n_edges = len(G.edges())
    max_res = [n_edges, 3]
    min_res = [0, 0]
    bidirect = cspy.BiDirectional(G, max_res, min_res)
    bidirect.run()
    print("")
    for (u, v) in G.edges():
        print(u, v, G.edges[u, v])
    print("subproblem")
    print(bidirect.path)
    print("cost =", bidirect.total_cost)
    print("resources =", bidirect.consumed_resources)
    if bidirect.total_cost < -(10 ** -5):
        more_routes = True
        new_route = nx.DiGraph(name=route_id + 1)
        nx.add_path(new_route, bidirect.path)
        # new_route = nx.relabel_nodes({"Source": 0, "Sink": 0})
        total_cost = 0
        for (i, j) in new_route.edges():
            edge_cost = G.edges[i, j]["cost"]
            total_cost += edge_cost
            new_route.edges[i, j]["cost"] = edge_cost
        new_route.graph["cost"] = total_cost
        routes.append(new_route)
        print("new route", new_route.edges())
        print("new route cost =", total_cost)
        return routes, more_routes, route_id + 1
    else:
        more_routes = False
        return routes, more_routes, route_id
