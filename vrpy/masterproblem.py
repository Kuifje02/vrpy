class _MasterProblemBase:
    """Base class for the master problems.

    Args:
        G (DiGraph): Underlying network.
        routes_with_node (dict): Keys : nodes ; Values : list of routes which contain the node
        routes (list): Current routes/variables/columns.
        drop_penalty (int, optional) : Value of penalty if node is dropped. Defaults to None.
        num_vehicles (int, optional): Maximum number of vehicles. Defaults to None.
        periodic (bool, optional): True if vertices are to be visited periodically. Defaults to False.
        minimize_global_span (bool, optional): True if global span (maximum distance) is minimized. Defaults to False.
        relax (bool, optional): True if variables are continuous. Defaults to True.
    """

    def __init__(
        self,
        G,
        routes_with_node,
        routes,
        drop_penalty,
        num_vehicles,
        periodic,
        minimize_global_span,
        solver,
    ):
        self.G = G
        self.routes_with_node = routes_with_node
        self.routes = routes
        self.drop_penalty = drop_penalty
        self.num_vehicles = num_vehicles
        self.periodic = periodic
        self.minimize_global_span = minimize_global_span
        self.solver = solver
