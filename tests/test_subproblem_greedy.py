from networkx import DiGraph

from vrpy.subproblem_greedy import _SubProblemGreedy


class TestsToy:
    def setup(self):
        self.G = DiGraph()
        self.G.add_edge("Source", 1, cost=[1], time=20)
        self.G.add_edge(1, 2, cost=[1], time=20)
        self.G.add_edge(2, "Sink", cost=[1], time=20)
        self.G.nodes[1]["demand"] = self.G.nodes[2]["demand"] = 2
        self.G.nodes["Source"]["demand"] = self.G.nodes["Sink"]["demand"] = 0
        self.prob = _SubProblemGreedy(self.G, {}, {1: [], 2: []}, [], 0)
        self.prob._initialize_run()

    def test_forward(self):
        self.prob.run_forward()
        assert self.prob._current_path == ["Source", 1, 2, "Sink"]

    def test_backwards(self):
        self.prob.run_backwards()
        assert self.prob._current_path == ["Source", 1, 2, "Sink"]

    def test_capacity(self):
        self.prob.load_capacity = [1]
        self.prob.run_forward()
        assert self.prob._current_path == ["Source"]
        self.prob._initialize_run()
        self.prob.run_backwards()
        assert self.prob._current_path == ["Sink"]

    def test_duration(self):
        self.prob.duration = 10
        self.prob.run_forward()
        assert self.prob._current_path == ["Source"]
        self.prob._initialize_run()
        self.prob.run_backwards()
        assert self.prob._current_path == ["Sink"]

    def test_stops(self):
        self.prob.num_stops = 1
        self.prob.run_forward()
        assert self.prob._current_path == ["Source", 1]
        self.prob._initialize_run()
        self.prob.run_backwards()
        assert self.prob._current_path == [2, "Sink"]

    def test_add_new_route(self):
        self.prob.run_forward()
        self.prob._add_new_route()
        assert set(self.prob.routes[0].nodes()) == {"Source", 1, 2, "Sink"}
        assert set(self.prob.routes_with_node[1][0].nodes()) == {"Source", 1, 2, "Sink"}
