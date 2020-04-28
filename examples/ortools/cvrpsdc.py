from base_ortools import OrToolsBase


class CVRPSDC(OrToolsBase):
    """
    VRP with simultaneous distribution and collection.
    https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118
    """

    def __init__(self):
        super(CVRPSDC, self).__init__()

        # set distribution volumes
        demand = [0, 1, 1, 2, 4, 2, 4, 8, 8, 1, 2, 1, 2, 4, 4, 8, 8]
        self.demand = dict(zip(self.nodes.keys(), demand))

        # set collect volumes
        collect = [0, 1, 1, 1, 1, 2, 1, 4, 1, 1, 2, 3, 2, 4, 2, 1, 2]
        self.collect = dict(zip(self.nodes.keys(), collect))

        # update options
        self.max_load = 15
        self.max_duration = 2300

        # update network
        self.G.graph["name"] += "cvrpsdc"
        self.update_demand_collect()

    def update_demand_collect(self):
        for node_id in self.nodes:
            if node_id > 0:
                self.G.nodes[node_id]["demand"] = self.demand[node_id]
                self.G.nodes[node_id]["collect"] = self.collect[node_id]

    def show_vehicle_loads(self):
        for r in self.best_routes:
            print("route ", r.graph["name"])
            print("========")
            for (i, j) in r.edges():
                if "load" in r.edges[i, j]:
                    print(
                        i, j, "total flow", r.edges[i, j]["load"],
                    )


if __name__ == "__main__":
    data = CVRPSDC()
    data.solve()
    data.show_vehicle_loads()
    data.plot_solution()
