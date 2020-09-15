from networkx import DiGraph, shortest_path

from vrpy.clarke_wright import _ClarkeWright, _RoundTrip
from vrpy.greedy import _Greedy


class TestsInitialSolution:
    """
    Initial solution can be computed with:
        - a round trip;
        - Clarke & Wright;
        - Greedy.
    """

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
        self.G.nodes["Sink"]["demand"] = self.G.nodes["Sink"]["service_time"] = 0
        self.G.nodes[1]["service_time"] = 1
        self.G.nodes[2]["service_time"] = 1
        self.G.nodes[3]["service_time"] = 0

        self.alg = _ClarkeWright(self.G, load_capacity=4)
        self.greedy = _Greedy(self.G, load_capacity=4)

    ##############
    # Round Trip #
    ##############

    def test_round_trip(self):
        round_trips = _RoundTrip(self.G)
        round_trips.run()
        assert len(round_trips.round_trips) == 3

    ###################
    # Clarke & Wright #
    ###################

    def test_initialization(self):
        self.alg._initialize_routes()
        assert self.alg._route[1].graph["load"] == self.G.nodes[1]["demand"]
        assert len(self.alg._route[1].nodes()) == 3

    def test_savings(self):
        self.alg._get_savings()
        assert self.alg._savings[(1, 2)] == 23
        assert self.alg._ordered_edges[0] == (1, 2)

    def test_result_load(self):
        self.alg.run()
        assert self.alg.best_value == 42
        assert shortest_path(self.alg._route[1], "Source", "Sink") == [
            "Source",
            1,
            2,
            "Sink",
        ]

    def test_result_duration(self):
        self.alg.duration = 4
        self.alg.run()
        assert self.alg.best_value == 50
        assert shortest_path(self.alg._route[1], "Source", "Sink") == [
            "Source",
            1,
            3,
            "Sink",
        ]

    def test_result_stops(self):
        self.alg.num_stops = 1
        self.alg.run()
        assert self.alg.best_value == 65
        assert shortest_path(self.alg._route[1], "Source", "Sink") == [
            "Source",
            1,
            "Sink",
        ]

    ##########
    # Greedy #
    ##########

    def test_greedy__load(self):
        self.greedy.run()
        assert self.greedy.best_value == 42
        assert self.greedy.best_routes[0] == ["Source", 1, 2, "Sink"]

    def test_greedy_duration(self):
        self.greedy.duration = 4
        self.greedy.run()
        assert self.greedy.best_value == 50
        assert self.greedy.best_routes[0] == ["Source", 1, 3, "Sink"]

    def test_greedy_stops(self):
        self.greedy.num_stops = 1
        self.greedy.run()
        assert self.greedy.best_routes[0] == ["Source", 1, "Sink"]
        assert self.greedy.best_value == 65
