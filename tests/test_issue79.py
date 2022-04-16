from networkx import DiGraph
from vrpy import VehicleRoutingProblem


class TestIssue79:

    def setup(self):
        G = DiGraph()
        G.add_edge("Source", 8, cost=0)
        G.add_edge("Source", 6, cost=1)
        G.add_edge("Source", 2, cost=1)
        G.add_edge("Source", 5, cost=1)
        G.add_edge(8, 6, cost=0)
        G.add_edge(6, 2, cost=0)
        G.add_edge(2, 5, cost=0)
        G.add_edge(5, "Sink", cost=0)
        G.add_edge(8, "Sink", cost=1)
        G.add_edge(6, "Sink", cost=1)
        G.add_edge(2, "Sink", cost=1)
        G.nodes[8]["demand"] = 8
        G.nodes[6]["demand"] = 4
        G.nodes[2]["demand"] = 1
        G.nodes[5]["demand"] = 2
        G.nodes[8]["collect"] = 1
        G.nodes[6]["collect"] = 1
        G.nodes[2]["collect"] = 1
        G.nodes[5]["collect"] = 2
        self.prob = VehicleRoutingProblem(G,
                                          load_capacity=15,
                                          distribution_collection=True)

    def test_node_load_cspy(self):
        self.prob.solve()
        assert self.prob.node_load[1][8] == 8
        assert self.prob.node_load[1][6] == 5
        assert self.prob.node_load[1][2] == 5
        assert self.prob.node_load[1][5] == 5

    def test_node_load_lp(self):
        self.prob.solve(cspy=False)
        assert self.prob.node_load[1][8] == 8
        assert self.prob.node_load[1][6] == 5
        assert self.prob.node_load[1][2] == 5
        assert self.prob.node_load[1][5] == 5
