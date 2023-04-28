from networkx import DiGraph
from vrpy import VehicleRoutingProblem
import networkx as nx

from networkx import DiGraph
from vrpy import VehicleRoutingProblem


class TestIssue147:
    def setup(self):
        G = DiGraph()
        for v in [1, 2, 3, 4]:
            G.add_edge("Source", v, cost=[10, 11, 10, 10])
            G.add_edge(v, "Sink", cost=[10, 11, 10, 10])
            G.nodes[v]["demand"] = 10
        G.add_edge(1, 2, cost=[10, 11, 10, 10])
        G.add_edge(2, 3, cost=[10, 11, 10, 10])
        G.add_edge(3, 4, cost=[15, 16, 10, 10])

        self.prob = VehicleRoutingProblem(
            G, mixed_fleet=True, load_capacity=[10, 10, 10, 10], use_all_vehicles=True
        )

    def test(self):
        self.prob.solve()
        assert self.prob.best_routes_type == {1: 0, 2: 1, 3: 2, 4: 3}

    def test_set_num_vehicles(self):
        self.prob.num_vehicles = [1, 1, 0, 2]
        self.prob.solve()
        assert set(self.prob.best_routes_type.values()) == set([0, 1, 3])
