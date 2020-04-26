from networkx import relabel_nodes, DiGraph, draw_networkx_edges, draw_networkx_nodes
import sys
import matplotlib.pyplot
import numpy as np

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class VRPTW:
    """
    Stores the data from ortools PDP example ;
    https://developers.google.com/optimization/routing/vrptw
    """

    def __init__(self):
        # data from ortools
        self.nodes = {
            0: (456, 320),  # location 0 - the depot
            1: (228, 0),  # location 1
            2: (912, 0),  # location 2
            3: (0, 80),  # location 3
            4: (114, 80),  # location 4
            5: (570, 160),  # location 5
            6: (798, 160),  # location 6
            7: (342, 240),  # location 7
            8: (684, 240),  # location 8
            9: (570, 400),  # location 9
            10: (912, 400),  # location 10
            11: (114, 480),  # location 11
            12: (228, 480),  # location 12
            13: (342, 560),  # location 13
            14: (684, 560),  # location 14
            15: (0, 640),  # location 15
            16: (798, 640),  # location 16
        }
        self.time_windows = {
            0: (0, 5),  # depot
            1: (7, 12),  # 1
            2: (10, 15),  # 2
            3: (16, 18),  # 3
            4: (10, 13),  # 4
            5: (0, 5),  # 5
            6: (5, 10),  # 6
            7: (0, 4),  # 7
            8: (5, 10),  # 8
            9: (0, 3),  # 9
            10: (10, 16),  # 10
            11: (10, 15),  # 11
            12: (0, 5),  # 12
            13: (5, 10),  # 13
            14: (7, 8),  # 14
            15: (10, 15),  # 15
            16: (11, 15),  # 16
        }
        self.duration = 25

        # create network
        self.G = DiGraph(name="ortools_vrptw")
        self.add_nodes()
        self.add_edges()

    def add_nodes(self):
        for id in self.nodes:
            x = self.nodes[id][0] / 114
            y = self.nodes[id][1] / 80
            if id == 0:
                self.G.add_node(
                    "Source", x=x, y=y, demand=0, service_time=0, lower=0, upper=5
                )
                self.G.add_node(
                    "Sink", x=x, y=y, demand=0, service_time=0, lower=0, upper=25
                )
            else:
                self.G.add_node(
                    id,
                    x=x,
                    y=y,
                    demand=0,
                    service_time=0,
                    lower=self.time_windows[id][0],
                    upper=self.time_windows[id][1],
                )

    def add_edges(self):
        for u in self.G.nodes():
            for v in self.G.nodes():
                if u != v:
                    self.G.add_edge(
                        u, v, cost=self.manhattan(u, v), time=self.manhattan(u, v)
                    )

    def manhattan(self, u, v):
        abs_x = abs(self.G.nodes[u]["x"] - self.G.nodes[v]["x"])
        abs_y = abs(self.G.nodes[u]["y"] - self.G.nodes[v]["y"])
        return abs_x + abs_y

    def solve(self, initial_routes=None, cspy=False, exact=True):
        """Instantiates instance as VRP and solves."""
        if cspy:
            self.G.graph["subproblem"] = "cspy"
        else:
            self.G.graph["subproblem"] = "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(
            self.G,
            initial_routes=initial_routes,
            duration=self.duration,
            edge_cost_function=self.manhattan,
            time_windows=True,
        )
        prob.solve(cspy=cspy, exact=exact)
        self.best_value, self.best_routes = prob.best_value, prob.best_routes
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

    def plot_solution(self):
        """Plots the solution after optimization."""
        # Store coordinates
        pos = {}
        for v in self.G.nodes():
            pos[v] = np.array([self.G.nodes[v]["x"], self.G.nodes[v]["y"]])

        # Draw customers
        draw_networkx_nodes(
            self.G, pos, node_size=10,
        )
        # Draw Source and Sink
        draw_networkx_nodes(
            self.G, pos, nodelist=["Source", "Sink"], node_size=50, node_color="r"
        )
        # Draw best routes
        options = {
            "node_color": "blue",
            "node_size": 10,
            "line_color": "grey",
            "linewidths": 0,
            "width": 0.1,
        }
        for r in self.best_routes:
            draw_networkx_edges(r, pos, **options)

        # matplotlib.pyplot.show() # Display best routes
        # Save best routes as image
        matplotlib.pyplot.savefig("%s.pdf" % self.G.graph["name"])


if __name__ == "__main__":
    data = VRPTW()
    # for (i, j) in data.G.edges():
    #    print(i, j, data.G.edges[i, j])
    initial_routes = [
        ["Source", 9, 14, 16, "Sink"],
        ["Source", 7, 1, 4, 3, "Sink"],
        ["Source", 12, 13, 15, 11, "Sink"],
        ["Source", 5, 8, 6, 2, 10, "Sink"],
    ]
    initial_routes = None
    data.solve(initial_routes=initial_routes, cspy=False)
    data.plot_solution()
