from networkx import DiGraph
import sys

sys.path.append("../")
sys.path.append("../vrpy/")
from vrpy.main import VRPSolver


class TestsToy:
    def setup(self):
        """
        Creates a toy graph and sets the initial routes for first iteration
        """
        self.G = DiGraph()
        for v in [1, 2, 3, 4, 5]:
            self.G.add_edge("Source", v, cost=10, time=20)
            self.G.add_edge(v, "Sink", cost=10, time=20)
            self.G.nodes[v]["demand"] = 5
            self.G.nodes[v]["upper"] = 100
            self.G.nodes[v]["lower"] = 0
        self.G.nodes[2]["upper"] = 20
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

    #################
    # subsolve cspy #
    #################

    def test_sub_cspy_stops(self):
        """Tests column generation procedure on toy graph with stop constraints"""
        prob = VRPSolver(self.G, num_stops=3)
        assert prob.column_generation() == 70

    def test_sub_cspy_stops_capacity(self):
        """Tests column generation procedure on toy graph
           with stop and capacity constraints
        """
        prob = VRPSolver(self.G, num_stops=3, load_capacity=10)
        assert prob.column_generation() == 80

    def test_sub_cspy_stops_capacity_duration(self):
        """Tests column generation procedure on toy graph
           with stop, capacity and duration constraints
        """
        prob = VRPSolver(self.G, num_stops=3, load_capacity=10, duration=60,)
        assert prob.column_generation() == 85

    def test_sub_cspy_stops_time_windows(self):
        """Tests column generation procedure on toy graph
           with stop, capacity and time_window constraints
        """
        prob = VRPSolver(self.G, num_stops=3, duration=60, time_windows=True,)
        assert prob.column_generation() == 80

    ###############
    # subsolve lp #
    ###############

    def test_LP_stops(self):
        """Tests column generation procedure on toy graph with stop constraints"""
        prob = VRPSolver(self.G, num_stops=3)
        assert prob.column_generation(cspy=False) == 70

    def test_LP_stops_capacity(self):
        """Tests column generation procedure on toy graph"""
        prob = VRPSolver(self.G, num_stops=3, load_capacity=10)
        assert prob.column_generation(cspy=False) == 80

    def test_LP_stops_capacity_duration(self):
        """Tests column generation procedure on toy graph"""
        prob = VRPSolver(self.G, num_stops=3, load_capacity=10, duration=60)
        assert prob.column_generation(cspy=False) == 85

    def test_LP_stops_time_windows(self):
        """Tests column generation procedure on toy graph"""
        prob = VRPSolver(self.G, num_stops=3, time_windows=True,)
        assert prob.column_generation(cspy=False) == 80
