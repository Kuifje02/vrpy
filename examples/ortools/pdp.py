from base_ortools import OrToolsBase


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
            1: 6,
            2: 10,
            4: 3,
            5: 9,
            7: 8,
            15: 11,
            13: 12,
            16: 14,
        }
        self.max_duration = 2200
        self.activate_pickup_delivery = True

        # update network
        self.G.graph["name"] += "pdp"
        self.add_pickup_delivery()

    def add_pickup_delivery(self):
        for node_id in self.nodes:
            if node_id in self.pickups_deliveries:
                self.G.nodes[node_id]["request"] = self.pickups_deliveries[node_id]


if __name__ == "__main__":

    data = PDP()
    initial_routes = []
    for pickup_node in data.pickups_deliveries:
        if pickup_node in data.G.nodes():
            initial_routes.append(
                ["Source", pickup_node, data.pickups_deliveries[pickup_node], "Sink"]
            )
    data.solve(initial_routes=initial_routes)
    data.plot_solution()
