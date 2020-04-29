import sys

sys.path.append("../../")
from examples.ortools.base_ortools import OrToolsBase


class VRPTW(OrToolsBase):
    """
    Stores the data from ortools PDP example ;
    https://developers.google.com/optimization/routing/vrptw
    """

    def __init__(self):
        super(VRPTW, self).__init__()

        # set time windows
        self.time_windows = {
            0: (0, 5),
            1: (7, 12),
            2: (10, 15),
            3: (16, 18),
            4: (10, 13),
            5: (0, 5),
            6: (5, 10),
            7: (0, 4),
            8: (5, 10),
            9: (0, 3),
            10: (10, 16),
            11: (10, 15),
            12: (0, 5),
            13: (5, 10),
            14: (7, 8),
            15: (10, 15),
            16: (11, 15),
        }

        # update constraints
        self.max_duration = 25
        self.activate_time_windows = True

        # update network
        self.G.graph["name"] += "vrptw"
        self.update_node_attributes()
        self.update_edge_attributes()

    def update_node_attributes(self):
        for node_id in self.nodes:
            x = self.nodes[node_id][0] / 114
            y = self.nodes[node_id][1] / 80
            if node_id == 0:
                for depot in ["Source", "Sink"]:
                    self.G.nodes[depot]["x"] = x
                    self.G.nodes[depot]["y"] = y
                    self.G.nodes[depot]["lower"] = self.time_windows[node_id][0]
                    self.G.nodes[depot]["upper"] = self.time_windows[node_id][1]
                self.G.nodes["Sink"]["upper"] = self.max_duration

            else:
                self.G.nodes[node_id]["x"] = x
                self.G.nodes[node_id]["y"] = y
                self.G.nodes[node_id]["lower"] = self.time_windows[node_id][0]
                self.G.nodes[node_id]["upper"] = self.time_windows[node_id][1]

    def update_edge_attributes(self):
        for (u, v) in self.G.edges():
            self.G.edges[u, v]["cost"] = self.manhattan(u, v)
            self.G.edges[u, v]["time"] = self.manhattan(u, v)

    def show_departure_times(self):
        for r in self.best_routes:
            for v in r.nodes():
                if "time" in r.nodes[v]:
                    print(
                        v,
                        ":",
                        self.G.nodes[v]["lower"],
                        "<=",
                        r.nodes[v]["time"],
                        "<=",
                        self.G.nodes[v]["upper"],
                    )


if __name__ == "__main__":
    data = VRPTW()
    initial_routes = [
        ["Source", 9, 14, 16, "Sink"],
        ["Source", 7, 1, 4, 3, "Sink"],
        ["Source", 12, 13, 15, 11, "Sink"],
        ["Source", 5, 8, 6, 2, 10, "Sink"],
    ]
    initial_routes = None
    data.solve(initial_routes=initial_routes, cspy=False)
    data.show_departure_times()
    data.plot_solution()
