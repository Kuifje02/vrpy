from networkx import DiGraph
import sys

sys.path.append("../../")
sys.path.append("../../../cspy")
from vrpy.main import VehicleRoutingProblem


class OrToolsBase:
    """
    Base class for the ortools examples ;
    https://developers.google.com/optimization/routing/
    """

    def __init__(self):
        # node positions
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
        # options
        self.max_duration = None
        self.max_load = None
        self.activate_pickup_delivery = False
        self.penalty = None
        self.activate_time_windows = False
        self.activate_distribution_collection = False

        # create network
        self.G = DiGraph(name="ortools_")
        self.add_nodes()
        self.add_edges()

    def add_nodes(self):
        """Adds nodes with their positions."""
        for node_id in self.nodes:
            x = self.nodes[node_id][0]
            y = self.nodes[node_id][1]
            if node_id == 0:
                self.G.add_node("Source", x=x, y=y, demand=0)
                self.G.add_node("Sink", x=x, y=y, demand=0)
            else:
                self.G.add_node(node_id, x=x, y=y, demand=0)

    def add_edges(self):
        """Adds all possible edges with cost and time attributes."""
        for u in self.G.nodes():
            for v in self.G.nodes():
                if u != v and u != "Sink" and v != "Source":
                    self.G.add_edge(
                        u, v, cost=self.manhattan(u, v), time=self.manhattan(u, v)
                    )

    def manhattan(self, u, v):
        """Computes Manhattan distance between to nodes."""
        abs_x = abs(self.G.nodes[u]["x"] - self.G.nodes[v]["x"])
        abs_y = abs(self.G.nodes[u]["y"] - self.G.nodes[v]["y"])
        return abs_x + abs_y

    def solve(
        self, initial_routes=None, cspy=False, exact=True, pricing_strategy="PrunePaths"
    ):
        """Instantiates instance as VRP and solves."""
        if cspy:
            self.G.graph["subproblem"] = "cspy"
        else:
            self.G.graph["subproblem"] = "lp"
        print(self.G.graph["name"], self.G.graph["subproblem"])
        print("===========")
        prob = VehicleRoutingProblem(
            self.G,
            duration=self.max_duration,
            load_capacity=self.max_load,
            drop_penalty=self.penalty,
            pickup_delivery=self.activate_pickup_delivery,
            distribution_collection=self.activate_distribution_collection,
            time_windows=self.activate_time_windows,
        )
        prob.solve(
            initial_routes=initial_routes,
            cspy=cspy,
            exact=exact,
            pricing_strategy=pricing_strategy,
        )
        self.best_value, self.best_routes = prob.best_value, prob._best_routes_as_graphs
