import sys
import time
import numpy as np
from math import sqrt
import matplotlib.pyplot
from pandas import read_csv
from networkx import DiGraph, draw_networkx_edges, draw_networkx_nodes

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class SolomonNode:
    """Stores attributes of a node of Solomon's instances."""

    def __init__(self, values):
        # Node ID
        self.name = np.uint32(values[1]).item()
        if self.name == 0:
            self.name = "Source"
        # x coordinate
        self.x = np.float64(values[2]).item()
        # y coordinate
        self.y = np.float64(values[3]).item()
        self.demand = np.uint32(values[4]).item()
        self.inf_time_window = np.uint32(values[5]).item()
        self.sup_time_window = np.uint32(values[6]).item()
        self.service_time = np.uint32(values[7]).item()


class DataSet:
    """Reads a Solomon instance and stores the network as DiGraph.

    Args:
        path (str) : Path to data folder.
        instance_name (str) : Name of Solomon instance to read.
        n_vertices (int, optional):
            Only first n_vertices are read.
            Defaults to None.
    """

    def __init__(self, path, instance_name, n_vertices=None):

        # Read vehicle capacity
        with open(path + instance_name) as fp:
            for i, line in enumerate(fp):
                if i == 4:
                    self.max_load = int(line.split()[1])
        fp.close()

        # Create network and store name + capacity
        self.G = DiGraph(
            name=instance_name[:-4] + "." + str(n_vertices),
            vehicle_capacity=self.max_load,
        )

        # Read nodes from txt file
        df_solomon = read_csv(
            path + instance_name,
            sep="\s+",
            skip_blank_lines=True,
            skiprows=7,
            nrows=n_vertices,
        )
        # Scan each line of the file and add nodes to the network
        for line in df_solomon.itertuples():
            node = SolomonNode(line)
            self.G.add_node(
                node.name,
                x=node.x,
                y=node.y,
                demand=node.demand,
                lower=node.inf_time_window,
                upper=node.sup_time_window,
                service_time=node.service_time,
            )
            # Add Sink as copy of Source
            if node.name == "Source":
                self.G.add_node(
                    "Sink",
                    x=node.x,
                    y=node.y,
                    demand=node.demand,
                    lower=node.inf_time_window,
                    upper=node.sup_time_window,
                    service_time=node.service_time,
                )

        # Add the edges, the graph is complete
        for u in self.G.nodes():
            if u != "Sink":
                for v in self.G.nodes():
                    if v != "Source":
                        if u != v and (u, v) != ("Source", "Sink"):
                            self.G.add_edge(u,
                                            v,
                                            cost=self.distance(u, v),
                                            time=self.distance(u, v))

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
        return sqrt(delta_x**2 + delta_y**2)

    def solve(self, num_stops=None, cspy=False):
        """Instantiates instance as VRP and solves."""
        if cspy:
            self.G.graph["subproblem"] = "cspy"
        else:
            self.G.graph["subproblem"] = "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(self.G,
                                     num_stops=num_stops,
                                     load_capacity=self.max_load,
                                     time_windows=True)
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
            self.G,
            pos,
            node_size=10,
        )
        # Draw Source and Sink
        draw_networkx_nodes(self.G,
                            pos,
                            nodelist=["Source", "Sink"],
                            node_size=50,
                            node_color="r")
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
    keys = ["instance", "nodes", "lp", "time (s)", "cspy", "time (s)"]
    instance = []
    nodes = []
    # LP
    res_lp = []
    time_lp = []
    # cspy
    res_cspy = []
    time_cspy = []

    for n in range(3, 12):
        solomon_data = DataSet(path="./data/",
                               instance_name="c101.txt",
                               n_vertices=n)
        instance.append(solomon_data.G.graph["name"])
        nodes.append(n)
        # LP
        start = time.time()
        solomon_data.solve(num_stops=None, cspy=False)
        time_lp.append(float(time.time() - start))
        res_lp.append(solomon_data.best_value)
        # cspy
        start = time.time()
        solomon_data.solve(num_stops=None, cspy=True)
        time_cspy.append(float(time.time() - start))
        res_cspy.append(solomon_data.best_value)

        # solomon_data.plot_solution()
    from pandas import DataFrame
    values = [instance, nodes, res_lp, time_lp, res_cspy, time_cspy]
    compar = dict(zip(keys, values))
    df = DataFrame(compar, columns=keys)
    df.to_excel("compar.xls", index=False)
