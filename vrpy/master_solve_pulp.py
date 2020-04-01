import pulp


def master_solve(G, routes, relax=True):
    """Solves the Master Problem for the column generation procedure

    Arguments:
        G: A networkx DiGraph
        routes: A list or routes/columns/variables

    Keyword Arguments:
        relax {bool} -- True if variables are continuous, False if binary (default: True)

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
                pulp.lpSum([y[r.graph["name"]] for r in routes if v in r.nodes()]) >= 1,
                "visit_node_%s" % v,
            )

    # solve problem
    # print(prob)
    # prob.writeLP("prob.lp")
    prob.solve()
    # if you have CPLEX
    # prob.solve(pulp.solvers.CPLEX_CMD(msg=0)))
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
        # print(pulp.value(prob.objective))
        return pulp.value(prob.objective)


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
