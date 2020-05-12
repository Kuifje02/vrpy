import sys

sys.path.append("../../")
from examples.ortools.base_ortools import OrToolsBase


class PDP(OrToolsBase):
    """
    Stores the data from ortools PDP example ;
    https://developers.google.com/optimization/routing/pickup_delivery
    """

    def __init__(self):
        super(PDP, self).__init__()

        # key = pickup node
        # value = delivery node
        self.pickups_deliveries = {
            (1, 6): 1,
            (2, 10): 2,
            (4, 3): 3,
            (5, 9): 1,
            (7, 8): 2,
            (15, 11): 3,
            (13, 12): 1,
            (16, 14): 4,
        }
        self.max_duration = 2200
        self.activate_pickup_delivery = True
        self.max_load = 10

        # update network
        self.G.graph["name"] += "pdp"
        self.add_pickup_delivery()

    def add_pickup_delivery(self):
        for (u, v) in self.pickups_deliveries:
            self.G.nodes[u]["request"] = v
            self.G.nodes[u]["demand"] = self.pickups_deliveries[(u, v)]
            self.G.nodes[v]["demand"] = -self.pickups_deliveries[(u, v)]


if __name__ == "__main__":
    import time

    data = PDP()
    start = time.time()
    data.solve(
        cspy=False, solver="cplex", pricing_strategy="Exact",
    )
    print(data.best_value)
    print(data.best_routes_nodes)
