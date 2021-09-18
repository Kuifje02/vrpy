from networkx import DiGraph
from vrpy import VehicleRoutingProblem


class TestIssue110:
    def setup(self):
        G = DiGraph()
        G.add_edge("Source", 1, cost=[1, 2])
        G.add_edge("Source", 2, cost=[2, 4])
        G.add_edge(1, "Sink", cost=[0, 0])
        G.add_edge(2, "Sink", cost=[2, 4])
        G.add_edge(1, 2, cost=[1, 2])
        G.nodes[1]["demand"] = 13
        G.nodes[2]["demand"] = 13
        self.prob = VehicleRoutingProblem(G, mixed_fleet=True, load_capacity=[10, 15])

    def test_node_load(self):
        self.prob.solve()
        assert self.prob.best_routes_type == {1: 1, 2: 1}
