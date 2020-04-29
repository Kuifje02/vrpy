import sys

sys.path.append("../../")
from examples.ortools.base_ortools import OrToolsBase


class VRP(OrToolsBase):
    """
    Stores the data from ortools VRP example ;
    https://developers.google.com/optimization/routing/vrp
    """

    def __init__(self):
        super(VRP, self).__init__()

        # update constraints
        self.max_duration = 1600

        # update network name
        self.G.graph["name"] += "vrp"


if __name__ == "__main__":
    data = VRP()
    initial_routes = [
        ["Source", 15, 14, 13, 16, "Sink"],
        ["Source", 9, 10, 11, 12, "Sink"],
        ["Source", 8, 1, 4, 3, "Sink"],
        ["Source", 7, 6, 2, 5, "Sink"],
    ]
    initial_routes = None
    data.solve(initial_routes=initial_routes)
    data.plot_solution()
