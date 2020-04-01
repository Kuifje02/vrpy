from networkx import DiGraph
import sys

sys.path.append("../vrpy")
from vrpy.vrpy import main


class TestsToy:

    def setup(self):
        """
        Creates a toy graph 
        """
        self.G = DiGraph()
        for v in [1, 2, 3, 4, 5]:
            self.G.add_edge("Source", v, cost=10, time=20)
            self.G.add_edge(v, "Sink", cost=10, time=20)
            self.G.nodes[v]["demand"] = 5
            self.G.nodes[v]["upper"] = 100
            self.G.nodes[v]["lower"] = 0
        self.G.nodes["Sink"]["demand"] = 0
        self.G.nodes["Sink"]["lower"] = 0
        self.G.nodes["Sink"]["upper"] = 100
        self.G.nodes["Source"]["demand"] = 0
        self.G.nodes["Source"]["lower"] = 0
        self.G.nodes["Source"]["upper"] = 100
        self.G.add_edge(1, 2, cost=10, time=20)
        self.G.add_edge(2, 3, cost=10, time=20)
        self.G.add_edge(3, 4, cost=15, time=20)
        self.G.add_edge(4, 5, cost=10, time=25)

    def test_missing_node(self):
        """Tests column generation procedure on toy graph"""
        self.G.remove_node(5)
        initial_routes = main.initialize_routes(self.G)
        best_value = main.main(self.G, initial_routes)
        assert best_value == 60

    def test_sub_cspy(self):
        """Tests column generation procedure on toy graph"""
        initial_routes = main.initialize_routes(self.G)
        best_value = main.main(self.G, initial_routes, cspy=True)
        assert best_value == 80

    def test_sub_pulp(self):
        """Tests column generation procedure on toy graph"""
        initial_routes = main.initialize_routes(self.G)
        best_value = main.main(self.G, initial_routes, max_load=True)
        assert best_value == 80
