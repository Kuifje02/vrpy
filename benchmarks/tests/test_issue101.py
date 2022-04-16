from networkx import DiGraph, read_gpickle
from vrpy import VehicleRoutingProblem


class TestIssue101_large:
    def setup(self):
        G = read_gpickle("benchmarks/tests/graph_issue101")
        self.prob = VehicleRoutingProblem(G, load_capacity=80)
        self.prob.time_windows = True

    # def test_lp(self):
    #     self.prob.solve(cspy=False, solver="gurobi")
    #     self.prob.check_arrival_time()
    #     self.prob.check_departure_time()

    def test_cspy(self):
        self.prob.solve(pricing_strategy="Exact")
        self.prob.check_arrival_time()
        self.prob.check_departure_time()
