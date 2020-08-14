from math import sqrt
from networkx import DiGraph, draw_networkx_edges, draw_networkx_nodes
import numpy as np
from pandas import read_csv
import sys
import matplotlib.pyplot

sys.path.append("../../")
sys.path.append("../../../cspy")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class CordeauNode:
    """Stores coordinates of a node of Cordeau's instances."""

    def __init__(self, values):
        # Node ID
        self.name = np.uint32(values[0]).item()
        # x coordinate
        self.x = np.float64(values[1]).item()
        # y coordinate
        self.y = np.float64(values[2]).item()
        # demand
        self.demand = np.uint32(values[4]).item()


class DataSet:
    """Reads a Cordeau instance and stores the network as DiGraph.

    Args:
        path (str) : Path to data folder.
        instance_name (str) : Name of instance to read.
        n_vertices (int, optional):
            Only first n_vertices are read.
            Defaults to None.
    """

    def __init__(self, path, instance_name, n_vertices=None):

        # Read vehicle capacity
        with open(path + instance_name) as fp:
            for i, line in enumerate(fp):
                if i == 0:
                    self.n_customers = int(line.split()[2])
                    if n_vertices is not None:
                        self.n_vertices = min(self.n_customers, n_vertices)
                    else:
                        self.n_vertices = self.n_customers
                elif i == 2:
                    self.max_load = int(line.split()[1])
        fp.close()

        # Create network and store name + capacity
        self.G = DiGraph(name=instance_name, vehicle_capacity=self.max_load,)

        # Read nodes from file
        df_cordeau = read_csv(path + instance_name, sep="\t", skiprows=4)
        # Scan each line of the file and add nodes to the network
        for line in df_cordeau.itertuples():
            values = line[1].split()
            node = CordeauNode(values)
            if node.name <= self.n_vertices:
                self.G.add_node(
                    node.name, x=node.x, y=node.y, demand=node.demand, customer=True
                )
            if node.name > self.n_customers:
                self.G.add_node(
                    node.name, x=node.x, y=node.y, demand=node.demand, depot_from=True
                )
                self.G.add_node(
                    str(node.name) + "_",
                    x=node.x,
                    y=node.y,
                    demand=node.demand,
                    depot_to=True,
                )

        # Add Source and Sink
        self.G.add_node("Source", x=0, y=0, demand=0)
        self.G.add_node("Sink", x=0, y=0, demand=0)

        # Add the edges, the graph is complete
        for u in self.G.nodes():
            if "customer" in self.G.nodes[u]:
                for v in self.G.nodes():
                    if "customer" in self.G.nodes[v] and u != v:
                        self.G.add_edge(u, v, cost=round(self.distance(u, v), 1))
            if "depot_to" in self.G.nodes[u]:
                self.G.add_edge(u, "Sink", cost=0)
                for v in self.G.nodes():
                    if "customer" in self.G.nodes[v]:
                        self.G.add_edge(v, u, cost=round(self.distance(v, u), 1))
            if "depot_from" in self.G.nodes[u]:
                self.G.add_edge("Source", u, cost=0)
                for v in self.G.nodes():
                    if "customer" in self.G.nodes[v]:
                        self.G.add_edge(u, v, cost=round(self.distance(u, v), 1))

    def distance(self, u, v):
        """2D Euclidian distance between two nodes.

        Args:
            u (Node) : tail node.
            v (Node) : head node.

        Returns:
            float : Euclidian distance between u and v
        """
        delta_x = self.G.nodes[u]["x"] - self.G.nodes[v]["x"]
        delta_y = self.G.nodes[u]["y"] - self.G.nodes[v]["y"]
        return sqrt(delta_x ** 2 + delta_y ** 2)

    def solve(self, initial_routes=None, cspy=False):
        """Instantiates instance as VRP and solves."""
        self.G.graph["subproblem"] = "cspy" if cspy else "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(self.G, load_capacity=self.max_load,)
        prob.solve(initial_routes=initial_routes, cspy=cspy)
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
        # Hide Source and Sink
        draw_networkx_nodes(
            self.G, pos, nodelist=["Source", "Sink"], node_size=0,
        )
        # Draw depots
        draw_networkx_nodes(
            self.G,
            pos,
            nodelist=[v for v in self.G.nodes() if "customer" not in self.G.nodes[v]],
            node_size=30,
            node_color="r",
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
            r.remove_edge("Source", list(r.successors("Source"))[0])
            r.remove_edge(list(r.predecessors("Sink"))[0], "Sink")
            draw_networkx_edges(r, pos, **options)

        # matplotlib.pyplot.show() # Display best routes
        # Save best routes as image
        matplotlib.pyplot.savefig("%s.pdf" % self.G.graph["name"])


if __name__ == "__main__":

    data = DataSet(path="./data/", instance_name="p01", n_vertices=8)
    ini = []
    # initial solution
    # ugly, needs more genericity
    for v in data.G.nodes():
        if "customer" in data.G.nodes[v]:
            ini.append(["Source", 51, v, str(51) + "_", "Sink"])

    data.solve(initial_routes=ini, cspy=False)
    data.plot_solution()
