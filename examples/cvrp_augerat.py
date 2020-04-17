from math import sqrt
from networkx import relabel_nodes, DiGraph, draw_networkx_edges, draw_networkx_nodes
import numpy as np
from pandas import read_csv
import sys
import matplotlib.pyplot

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class AugeratNodePosition:
    """Stores coordinates of a node of Augerat's instances (set P)."""

    def __init__(self, values):
        # Node ID
        self.name = np.uint32(values[0]).item()
        if self.name == 1:
            self.name = "Source"
        # x coordinate
        self.x = np.float64(values[1]).item()
        # y coordinate
        self.y = np.float64(values[2]).item()


class AugeratNodeDemand:
    """Stores attributes of a node of Augerat's instances (set P)."""

    def __init__(self, values):
        # Node ID
        self.name = np.uint32(values[0]).item()
        if self.name == 1:
            self.name = "Source"
        # demand coordinate
        self.demand = np.float64(values[1]).item()


class DataSet:
    """Reads an Augerat instance and stores the network as DiGraph.

    Args:
        path (str) : Path to data folder.
        instance_name (str) : Name of instance to read.
    """

    def __init__(self, path, instance_name):

        # Read vehicle capacity
        with open(path + instance_name) as fp:
            for i, line in enumerate(fp):
                if i == 5:
                    self.max_load = int(line.split()[2])
        fp.close()

        # Create network and store name + capacity
        self.G = DiGraph(name=instance_name[:-4], vehicle_capacity=self.max_load,)

        # Read nodes from txt file
        n_vertices = int(instance_name[3:5])
        df_augerat = read_csv(
            path + instance_name,
            sep="\t",
            # skip_blank_lines=True,
            skiprows=6,
            nrows=n_vertices,
            engine="python",
        )
        # Scan each line of the file and add nodes to the network
        for line in df_augerat.itertuples():
            values = line[1].split()
            node = AugeratNodePosition(values)
            self.G.add_node(node.name, x=node.x, y=node.y, demand=0)
            # Add Sink as copy of Source
            if node.name == "Source":
                self.G.add_node("Sink", x=node.x, y=node.y, demand=0)

        # Read demand from txt file
        n_vertices = int(instance_name[3:5])
        df_demand = read_csv(
            path + instance_name,
            sep="\t",
            # skip_blank_lines=True,
            skiprows=23,
        )
        for line in df_demand.itertuples():
            # print(line)
            values = line[1].split()
            try:
                node = AugeratNodeDemand(values)
                self.G.nodes[node.name]["demand"] = node.demand
            except:
                continue
        # Add the edges, the graph is complete
        for u in self.G.nodes():
            if u != "Sink":
                for v in self.G.nodes():
                    if v != "Source":
                        if u != v and (u, v) != ("Source", "Sink"):
                            self.G.add_edge(u, v, cost=round(self.distance(u, v), 1))

        # relabel
        before = [v for v in self.G.nodes() if v not in ["Source", "Sink"]]
        after = [v - 1 for v in self.G.nodes() if v not in ["Source", "Sink"]]
        mapping = dict(zip(before, after))
        self.G = relabel_nodes(self.G, mapping)

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
        if cspy:
            self.G.graph["subproblem"] = "cspy"
        else:
            self.G.graph["subproblem"] = "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(
            self.G,
            initial_routes=initial_routes,
            edge_cost_function=self.distance,
            load_capacity=self.max_load,
        )
        prob.solve(cspy=cspy)
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

    data = DataSet(path="./data/", instance_name="P-n16-k8.vrp")

    r_1 = ["Source", 2, "Sink"]
    r_2 = ["Source", 6, "Sink"]
    r_3 = ["Source", 8, "Sink"]
    r_4 = ["Source", 15, 12, 10, "Sink"]
    r_5 = ["Source", 14, 5, "Sink"]
    r_6 = ["Source", 13, 9, 7, "Sink"]
    r_7 = ["Source", 11, 4, "Sink"]
    r_8 = ["Source", 3, 1, "Sink"]
    ini = [r_1, r_2, r_3, r_4, r_5, r_6, r_7, r_8]
    # ini = None
    data.solve(initial_routes=ini, cspy=False)
    data.plot_solution()
