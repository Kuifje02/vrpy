from networkx import DiGraph
from vrpy import VehicleRoutingProblem


class TestIssue86:
    def setup(self):
        G = DiGraph()
        G.add_edge(1, 2, cost=77.67)
        G.add_edge(1, 3, cost=0.0)
        G.add_edge(1, 4, cost=96.61)
        G.add_edge(1, 5, cost=0.0)
        G.add_edge(1, 6, cost=59.03)
        G.add_edge(2, 1, cost=77.67)
        G.add_edge(2, 3, cost=77.67)
        G.add_edge(2, 4, cost=64.85)
        G.add_edge(2, 5, cost=77.67)
        G.add_edge(2, 6, cost=62.2)
        G.add_edge(3, 1, cost=0.0)
        G.add_edge(3, 2, cost=77.67)
        G.add_edge(3, 4, cost=96.61)
        G.add_edge(3, 5, cost=0.0)
        G.add_edge(3, 6, cost=59.03)
        G.add_edge(4, 1, cost=96.61)
        G.add_edge(4, 2, cost=64.85)
        G.add_edge(4, 3, cost=96.61)
        G.add_edge(4, 5, cost=96.61)
        G.add_edge(4, 6, cost=39.82)
        G.add_edge(5, 1, cost=0.0)
        G.add_edge(5, 2, cost=77.67)
        G.add_edge(5, 3, cost=0.0)
        G.add_edge(5, 4, cost=96.61)
        G.add_edge(5, 6, cost=59.03)
        G.add_edge(6, 1, cost=59.03)
        G.add_edge(6, 2, cost=62.2)
        G.add_edge(6, 3, cost=59.03)
        G.add_edge(6, 4, cost=39.82)
        G.add_edge(6, 5, cost=59.03)
        G.add_edge("Source", 1, cost=18.03)
        G.add_edge(1, "Sink", cost=18.93)
        G.add_edge("Source", 2, cost=61.29)
        G.add_edge(2, "Sink", cost=61.29)
        G.add_edge("Source", 3, cost=18.03)
        G.add_edge(3, "Sink", cost=18.03)
        G.add_edge("Source", 4, cost=79.92)
        G.add_edge(4, "Sink", cost=79.92)
        G.add_edge("Source", 5, cost=18.03)
        G.add_edge(5, "Sink", cost=18.03)
        G.add_edge("Source", 6, cost=44.38)
        G.add_edge(6, "Sink", cost=44.38)
        G.nodes[1]["request"] = 2
        G.nodes[1]["demand"] = 25000
        G.nodes[2]["demand"] = -25000
        G.nodes[3]["request"] = 4
        G.nodes[3]["demand"] = 25000
        G.nodes[4]["demand"] = -25000
        G.nodes[5]["request"] = 6
        G.nodes[5]["demand"] = 10000
        G.nodes[6]["demand"] = -10000
        self.prob = VehicleRoutingProblem(G, load_capacity=25000, pickup_delivery=True)

    def test_solve(self):
        self.prob.solve(cspy=False, solver="cbc")
        assert round(self.prob.best_value, 0) == 468
