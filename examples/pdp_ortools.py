from networkx import DiGraph, draw_networkx_edges, draw_networkx_nodes
import sys
import matplotlib.pyplot
import numpy as np

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class PDP:
    """
    Stores the data from ortools PDP example ;
    https://developers.google.com/optimization/routing/pickup_delivery
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
        self.duration = 2200

        # create network
        self.G = DiGraph(name="ortools_pdp")
        self.add_nodes()
        self.add_edges()

    def add_nodes(self):
        for node_id in self.nodes:
            x = self.nodes[node_id][0]
            y = self.nodes[node_id][1]
            if node_id == 0:
                self.G.add_node("Source", x=x, y=y, service_time=0)
                self.G.add_node("Sink", x=x, y=y, service_time=0)
            else:
                self.G.add_node(node_id, x=x, y=y, service_time=0)
            if node_id in self.pickups_deliveries:
                self.G.nodes[node_id]["request"] = self.pickups_deliveries[node_id]

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
    data = PDP()
    initial_routes = []
    for pickup_node in data.pickups_deliveries:
        if pickup_node in data.G.nodes():
            initial_routes.append(
                ["Source", pickup_node, data.pickups_deliveries[pickup_node], "Sink"]
            )
    data.solve(initial_routes=initial_routes)
    data.plot_solution()
