from base_ortools import OrToolsBase


class CVRP(OrToolsBase):
    """
    Stores the data from ortools CVRP example ;
    https://developers.google.com/optimization/routing/cvrp
    """

    def __init__(self):
        super(CVRP, self).__init__()
        # set demands
        demands = [0, 1, 1, 2, 4, 2, 4, 8, 8, 1, 2, 1, 2, 4, 4, 8, 8]
        self.demands = dict(zip(self.nodes.keys(), demands))
        # update options
        self.max_load = 15
        self.max_duration = 2300

        # update network
        self.G.graph["name"] += "cvrp"
        self.update_demands()

    def update_demands(self):
        for node_id in self.nodes:
            if node_id > 0:
                self.G.nodes[node_id]["demand"] = self.demands[node_id]

    def show_vehicle_loads(self):
        for r in self.best_routes:
            print(
                r.nodes(),
                sum([self.G.nodes[v]["demand"] for v in r.nodes()]),
                "<=",
                self.max_load,
            ),


if __name__ == "__main__":
    data = CVRP()
    initial_routes = [
        ["Source", 1, 4, 3, 15, "Sink"],
        ["Source", 14, 16, 10, 2, "Sink"],
        ["Source", 7, 13, 12, 11, "Sink"],
        ["Source", 9, 8, 6, 5, "Sink"],
    ]
    # initial_routes = None
    data.solve(initial_routes=initial_routes)
    data.show_vehicle_loads()
    data.plot_solution()
