from networkx import DiGraph
from vrpy import VehicleRoutingProblem


class TestIssue101_small:
    def setup(self):
        self.G = DiGraph()
        self.G.add_edge("Source", 1, cost=5)
        self.G.add_edge("Source", 2, cost=5)
        self.G.add_edge(1, "Sink", cost=5)
        self.G.add_edge(2, "Sink", cost=5)
        self.G.add_edge(1, 2, cost=1)
        self.G.nodes[1]["lower"] = 0
        self.G.nodes[1]["upper"] = 20
        self.G.nodes[2]["lower"] = 0
        self.G.nodes[2]["upper"] = 20
        self.G.nodes[1]["service_time"] = 5
        self.G.nodes[2]["service_time"] = 5
        self.G.nodes[1]["demand"] = 8
        self.G.nodes[2]["demand"] = 8
        self.prob = VehicleRoutingProblem(self.G, load_capacity=10, time_windows=True)

    def test_cspy(self):
        self.prob.solve()
        self.prob.check_arrival_time()
        self.prob.check_departure_time()

    def test_lp(self):
        self.prob.solve(cspy=False)
        self.prob.check_arrival_time()
        self.prob.check_departure_time()
