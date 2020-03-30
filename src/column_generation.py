import networkx as nx
import numpy as np
import pulp
import cspy


def master_solve(G, routes, relax=True):
    """Solves the Master Problem for the column generation procedure
    
    Arguments:
        G: A networkx DiGraph
        routes: A list or routes/columns/variables
    
    Keyword Arguments:
        relax {bool} -- [True if variables are continuous, False if binary] (default: {True})
    
    Returns:
        tuple -- A dict of duals and the objective function value
    """

    # create problem
    prob = pulp.LpProblem("MasterProblem", pulp.LpMinimize)

    # vartype represents whether or not the variables are relaxed
    if relax:
        vartype = pulp.LpContinuous
    else:
        vartype = pulp.LpInteger

    # create variables
    _routes = []
    for r in routes:
        _routes.append(r.graph["name"])
    y = pulp.LpVariable.dicts("y", _routes, lowBound=0, upBound=1, cat=vartype)

    # cost function
    prob += pulp.lpSum([y[r.graph["name"]] * r.graph["cost"] for r in routes])

    # visit each node once
    for v in G.nodes():
        if v not in ["Source", "Sink"]:  # v > 0:
            prob += (
                pulp.lpSum([y[r.graph["name"]] for r in routes if v in r.nodes()]) == 1,
                "visit_node_%s" % v,
            )

    # export problem as .lp
    prob.writeLP("prob.lp")

    # solve problem
    print(prob)
    prob.solve()  # pulp.solvers.CPLEX_CMD(msg=0))
    print("master problem")
    print("Status:", pulp.LpStatus[prob.status])
    print("Objective:", pulp.value(prob.objective))

    if relax:
        for r in routes:
            if pulp.value(y[r.graph["name"]]) > 0.5:
                print("route", r.graph["name"], "selected")
        duals = get_duals(prob, G)
        print(duals)
        # print(pulp.value(prob.objective))
        return duals, pulp.value(prob.objective)

    else:
        for r in routes:
            val = pulp.value(y[r.graph["name"]])
            if val > 0:
                print(r.edges(), "cost", r.graph["cost"])
        print(pulp.value(prob.objective))
        return


def get_duals(prob, G):
    """Gets the dual values of each constraint of the Master Problem
    
    Arguments:
        prob {pulp.LpProblem} -- The Master Problem
        G {networkx.DiGraph} 
    
    Returns:
        duals -- A dictionary of duals with constraint names as keys and duals as values
    """
    duals = {}
    for v in G.nodes():
        if v not in ["Source", "Sink"]:  # v > 0:
            constr_name = "visit_node_%s" % v
            duals[v] = prob.constraints[constr_name].pi
    return duals


def sub_solve_lp(G, duals, routes, route_id):
    """Solves the sub problem for the column generation procedure ; attemps
    to find routes with negative reduced cost
    
    Arguments:
        G {networkx.DiGraph} -- Graph representing the network
        duals {dict} -- Dictionary of dual values of master problem
        routes {list} -- List of current routes/variables/columns
        route_id {int} -- Last route ID number used
    
    Returns:
        routes, more_routes, route_id -- updated routes, boolean as True if new route was found, route ID number of found route
    """
    # create problem
    prob = pulp.LpProblem("SubProblem", pulp.LpMinimize)
    # flow variables
    x = pulp.LpVariable.dicts("x", G.edges(), cat=pulp.LpBinary)
    # minimize reduced cost
    edge_cost = pulp.lpSum([G.edges[i, j]["cost"] * x[(i, j)] for (i, j) in G.edges()])
    dual_cost = pulp.lpSum(
        [
            x[(v, j)] * duals[v]
            for v in G.nodes()
            if v not in ["Source"]
            for j in G.successors(v)
        ]
    )
    prob += edge_cost - dual_cost
    # flow balance
    for v in G.nodes():
        if v not in ["Source", "Sink"]:
            in_flow = pulp.lpSum([x[(i, v)] for i in G.predecessors(v)])
            out_flow = pulp.lpSum([x[(v, j)] for j in G.successors(v)])
            prob += in_flow == out_flow, "flow_balance_%s" % v

    # max 2 clients
    prob += pulp.lpSum([x[(i, j)] for (i, j) in G.edges()]) <= 3, "max_2"

    # export problem as .lp
    # print(prob)
    prob.writeLP("prob.lp")

    # solve problem
    # print(prob)
    prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
    print("")
    print("sub problem")
    print("Status:", pulp.LpStatus[prob.status])
    print("Objective:", pulp.value(prob.objective))

    if pulp.value(prob.objective) < -(10 ** -5):
        more_routes = True
        new_route = nx.DiGraph(name=route_id + 1)
        total_cost = 0
        for (i, j) in G.edges():
            if pulp.value(x[(i, j)]) > 0.5:
                # print(i, j, pulp.value(x[(i, j)]))
                edge_cost = G.edges[i, j]["cost"]
                total_cost += edge_cost
                new_route.add_edge(i, j, cost=edge_cost)
        new_route.graph["cost"] = total_cost
        routes.append(new_route)
        print("new route", new_route.edges())  # nx.shortest_path(new_route, 0))
        print("new route cost =", total_cost)

        return routes, more_routes, route_id + 1
    else:
        more_routes = False
        return routes, more_routes, route_id


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
