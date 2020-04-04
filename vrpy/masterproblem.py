from networkx import DiGraph


class MasterProblemBase:
    """Base class for the master problems.

    Attributes:
        G (DiGraph): Underlying network.
        routes (list): Current routes/variables/columns.
        relax (bool, optional): True if variables are continuous. Defaults to True.

    Args:
        G (DiGraph): Underlying network.
        routes (list): Current routes/variables/columns.
        relax (bool, optional): True if variables are continuous. Defaults to True.
    """

    def __init__(self, G, routes, relax):
        self.G = G
        self.routes = routes
        self.relax = relax
