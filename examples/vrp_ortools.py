from networkx import DiGraph, draw_networkx_edges, draw_networkx_nodes
import sys
import matplotlib.pyplot
import numpy as np

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class VRP:
    """
    Stores the data from ortools example ;
    https://developers.google.com/optimization/routing/vrp
    """

    def __init__(self):
        # node positions
        self.nodes = [
            (456, 320),  # location 0 - the depot
            (228, 0),  # location 1
            (912, 0),  # location 2
            (0, 80),  # location 3
            (114, 80),  # location 4
            (570, 160),  # location 5
            (798, 160),  # location 6
            (342, 240),  # location 7
            (684, 240),  # location 8
            (570, 400),  # location 9
            (912, 400),  # location 10
            (114, 480),  # location 11
            (228, 480),  # location 12
            (342, 560),  # location 13
            (684, 560),  # location 14
            (0, 640),  # location 15
            (798, 640),  # location 16
        ]
        self.max_duration = 1600

        # create network
        self.G = DiGraph(name="ortools_vrp")
        self.add_nodes()
        self.add_edges()

    def add_nodes(self):
        id = 0
        for (x, y) in self.nodes:
            if id == 0:
                self.G.add_node("Source", x=x, y=y, demand=0)
                self.G.add_node("Sink", x=x, y=y, demand=0)
            else:
                self.G.add_node(id, x=x, y=y, demand=0)
            id += 1

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
            edge_cost_function=self.manhattan,
            duration=self.max_duration,
        )
        prob.solve(cspy=cspy, exact=exact)
        self.best_value, self.best_routes = prob.best_value, prob.best_routes

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
    data = VRP()
    initial_routes = [
        ["Source", 15, 14, 13, 16, "Sink"],
        ["Source", 9, 10, 11, 12, "Sink"],
        ["Source", 8, 1, 4, 3, "Sink"],
        ["Source", 7, 6, 2, 5, "Sink"],
    ]
    # initial_routes = None
    data.solve(initial_routes=initial_routes)
    data.plot_solution()
