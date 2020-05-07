from networkx import DiGraph, shortest_path
import sys

sys.path.append("../../vrpy/")
from vrpy.clark_wright import ClarkWright, RoundTrip


class TestsClarkWright:
    def setup(self):
        self.G = DiGraph()
        self.G.add_edge("Source", 1, cost=10, time=1)
        self.G.add_edge("Source", 2, cost=15, time=1)
        self.G.add_edge("Source", 3, cost=15, time=1)
        self.G.add_edge(1, "Sink", cost=10, time=1)
        self.G.add_edge(2, "Sink", cost=5, time=1)
        self.G.add_edge(3, "Sink", cost=10, time=1)
        self.G.add_edge(1, 2, cost=2, time=5)
        self.G.add_edge(1, 3, cost=10, time=1)
        self.G.nodes[1]["demand"] = 1
        self.G.nodes[2]["demand"] = 2
        self.G.nodes[3]["demand"] = 3
        self.G.nodes[1]["service_time"] = 1
        self.G.nodes[2]["service_time"] = 1
        self.G.nodes[3]["service_time"] = 0

        self.alg = ClarkWright(self.G, load_capacity=4)

    def test_round_trip(self):
        round_trips = RoundTrip(self.G)
        round_trips.run()
        assert round_trips.route[1][0].graph["cost"] == 20
        assert len(round_trips.round_trips) == 3

    def test_initialization(self):
        self.alg.initialize_routes()
        assert self.alg.route[1].graph["load"] == self.G.nodes[1]["demand"]
        assert len(self.alg.route[1].nodes()) == 3

    def test_savings(self):
        self.alg.get_savings()
        assert self.alg.savings[(1, 2)] == 23
        assert self.alg.ordered_edges[0] == (1, 2)

    def test_result_load(self):
        self.alg.run()
        assert self.alg.best_value == 42
        assert shortest_path(self.alg.route[1][0], "Source", "Sink") == [
            "Source",
            1,
            2,
            "Sink",
        ]

    def test_result_duration(self):
        self.alg.duration = 4
        self.alg.run()
        assert self.alg.best_value == 50
        assert shortest_path(self.alg.route[1][0], "Source", "Sink") == [
            "Source",
            1,
            3,
            "Sink",
        ]

    def test_result_stops(self):
        self.alg.num_stops = 1
        self.alg.run()
        assert self.alg.best_value == 65
        assert shortest_path(self.alg.route[1][0], "Source", "Sink") == [
            "Source",
            1,
            "Sink",
        ]
