def get_num_stops_upper_bound(G,
                              max_capacity,
                              num_stops=None,
                              distribution_collection=False):
    """
    Finds upper bound on number of stops, from here :
    https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118

    A knapsack problem is solved to maximize the number of
    visits, subject to capacity constraints.
    """
    # Maximize sum of vertices such that sum of demands respect capacity constraints
    demands = [int(G.nodes[v]["demand"]) for v in G.nodes()]
    # Solve the knapsack problem
    max_num_stops = _knapsack(demands, max_capacity)
    if distribution_collection:
        collect = [int(G.nodes[v]["collect"]) for v in G.nodes()]
        max_num_stops = min(max_num_stops, _knapsack(collect, max_capacity))
    # Update num_stops attribute
    if num_stops:
        num_stops = min(max_num_stops, num_stops)
    else:
        num_stops = max_num_stops
    return num_stops


def _knapsack(weights, capacity):
    """
        Binary knapsack solver with identical profits of weight 1.
        Args:
            weights (list) : list of integers
            capacity (int) : maximum capacity
        Returns:
            (int) : maximum number of objects
        """
    n = len(weights)
    # sol : [items, remaining capacity]
    sol = [[0] * (capacity + 1) for i in range(n)]
    added = [[False] * (capacity + 1) for i in range(n)]
    for i in range(n):
        for j in range(capacity + 1):
            if weights[i] > j:
                sol[i][j] = sol[i - 1][j]
            else:
                sol_add = 1 + sol[i - 1][j - weights[i]]
                if sol_add > sol[i - 1][j]:
                    sol[i][j] = sol_add
                    added[i][j] = True
                else:
                    sol[i][j] = sol[i - 1][j]
    return sol[n - 1][capacity]
