import networkx as nx
import pulp


def sub_solve_lp(
    G, duals, routes, route_id, max_stop=True, max_load=False, max_time=False
):
    """Solves the sub problem for the column generation procedure ; attemps
    to find routes with negative reduced cost
    
    Arguments:
        G {networkx.DiGraph} -- Graph representing the network
        duals {dict} -- Dictionary of dual values of master problem
        routes {list} -- List of current routes/variables/columns
        route_id {int} -- Last route ID number used

    Keyword Arguments:
        max_stop {bool} -- True if stop constraints activated
        max_load {bool} -- True if capacity constraints activated
        max_time {bool} -- True if time constraints activated
    
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

    # max 3 stops
    if max_stop:
        prob += pulp.lpSum([x[(i, j)] for (i, j) in G.edges()]) <= 4, "max_3"

    # capacity constraints
    if max_load:
        prob += (
            pulp.lpSum([G.nodes[j]["demand"] * x[(i, j)] for (i, j) in G.edges()])
            <= 10,
            "max_load_10",
        )

    # time constraints
    if max_time:
        prob += (
            pulp.lpSum([G.edges[i, j]["time"] * x[(i, j)] for (i, j) in G.edges()])
            <= 60,
            "max_duration_60",
        )

    # solve problem
    # print(prob)
    # prob.writeLP("prob.lp")
    prob.solve()
    # if you have CPLEX
    # prob.solve(pulp.solvers.CPLEX_CMD(msg=0))
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
        print("new route", new_route.edges())
        print("new route cost =", total_cost)

        return routes, more_routes, route_id + 1
    else:
        more_routes = False
        return routes, more_routes, route_id
