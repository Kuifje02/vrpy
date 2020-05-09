from math import sqrt
from networkx import relabel_nodes, DiGraph
import numpy as np
from pandas import read_csv
import sys

sys.path.append("../../")
sys.path.append("../../../cspy")
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
                if i == 1:
                    best = line.split()[-1][:-1]
                    self.best_known_solution = int(best)
                if i == 5:
                    self.max_load = int(line.split()[2])
        fp.close()

        # Create network and store name + capacity
        self.G = DiGraph(name=instance_name[:-4], vehicle_capacity=self.max_load,)

        # Read nodes from txt file
        if instance_name[5] == "-":
            n_vertices = int(instance_name[3:5])
        else:
            n_vertices = int(instance_name[3:6])
        df_augerat = read_csv(
            path + instance_name, sep="\t", skiprows=6, nrows=n_vertices,
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
        df_demand = read_csv(
            path + instance_name,
            sep="\t",
            skiprows=range(7 + n_vertices),
            nrows=n_vertices,
        )
        for line in df_demand.itertuples():
            values = line[1].split()
            node = AugeratNodeDemand(values)
            self.G.nodes[node.name]["demand"] = node.demand

        # Add the edges, the graph is complete
        for u in self.G.nodes():
            if u != "Sink":
                for v in self.G.nodes():
                    if v != "Source":
                        if u != v:
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
        return round(sqrt(delta_x ** 2 + delta_y ** 2), 0)

    def solve(
        self,
        initial_routes=None,
        cspy=False,
        num_stops=None,
        exact=True,
        time_limit=None,
        pricing_strategy="PrunePaths",
    ):
        """Instantiates instance as VRP and solves."""
        if cspy:
            self.G.graph["subproblem"] = "cspy"
        else:
            self.G.graph["subproblem"] = "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(
            self.G, load_capacity=self.max_load, num_stops=num_stops,
        )
        prob.solve(
            initial_routes=initial_routes,
            edge_cost_function=self.distance,
            cspy=cspy,
            exact=exact,
            time_limit=time_limit,
            pricing_strategy=pricing_strategy,
        )
        self.best_value, self.best_routes = prob.best_value, prob.best_routes
