import sys

sys.path.append("../../")
from examples.ortools.cvrp import CVRP


class Drop(CVRP):
    """
    Stores the data from ortools CVRP example with penalties ;
    https://developers.google.com/optimization/routing/penalties
    Some vertices can be dropped, activating a penalty.
    """

    def __init__(self):
        super(Drop, self).__init__()

        # set demands
        demands = [0, 1, 1, 3, 6, 3, 6, 8, 8, 1, 2, 1, 2, 6, 6, 8, 8]
        self.demands = dict(zip(self.nodes.keys(), demands))
        self.penalty = 1000

        # update network
        self.G.graph["name"] += "_drop"
        self.update_demands()


if __name__ == "__main__":
    data = Drop()
    initial_routes = [
        ["Source", 9, 14, 16, "Sink"],
        ["Source", 12, 11, 4, 3, 1, "Sink"],
        ["Source", 7, 13, "Sink"],
        ["Source", 8, 10, 2, 5, "Sink"],
    ]
    # initial_routes = None
    data.solve(initial_routes=initial_routes)
    data.show_vehicle_loads()
    data.plot_solution()
