class SubProblemBase:
    """
    Base class for the subproblems.
    
    Arguments:
        G {networkx.DiGraph} -- Graph representing the network
        duals {dict} -- Dictionary of dual values of master problem
        routes {list} -- List of current routes/variables/columns

    Keyword Arguments:
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
        routes, more_routes -- updated routes, boolean as True if new route was found
    """

    def __init__(self,
                 G,
                 duals,
                 routes,
                 num_stops=None,
                 load_capacity=None,
                 duration=None,
                 time_windows=False):
        # Input attributes
        self.G = G
        self.duals = duals
        self.routes = routes
        self.num_stops = num_stops
        self.load_capacity = load_capacity
        self.duration = duration
        self.time_windows = time_windows
