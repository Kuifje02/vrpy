class MasterProblemBase:
    """Base class for the master problems.

    Args:
        G (DiGraph): Underlying network.
        routes (list): Current routes/variables/columns.
        drop_penalty (int, optional) : Value of penalty if node is dropped. Defaults to None.
        relax (bool, optional): True if variables are continuous. Defaults to True.
    """

    def __init__(self, G, routes, drop_penalty=None, relax=True):
        self.G = G
        self.routes = routes
        self.drop_penalty = drop_penalty
        self.relax = relax
