from math import sqrt
from networkx import DiGraph
import numpy as np
from pandas import read_csv
import sys

sys.path.append("../vrpy/")
sys.path.append("../")
from vrpy.main import VehicleRoutingProblem


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

        self.G = DiGraph()

        # Read txt file
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
                            self.G.add_edge(
                                u, v, cost=self.distance(u, v), time=self.distance(u, v)
                            )

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


"""
if __name__ == "__main__":
    solomon_data = DataSet(path="./", instance_name="c101.txt", n_vertices=3)
    G = solomon_data.G
    prob = VehicleRoutingProblem(G)
    prob.solve(cspy=False, max_iter=3)
"""
