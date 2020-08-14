from pytest import fixture

from vrpy import VehicleRoutingProblem

from benchmarks.solomon_dataset import SolomonDataSet

params = list(range(7, 10))


@fixture(
    scope="class",
    params=params,
)
def n(request):
    print("setup once per each param", request.param)
    return request.param


class TestsSolomon:
    def test_subproblem(self, n):
        data = SolomonDataSet(path="benchmarks/data/cvrptw/",
                              instance_name="C101.txt",
                              n_vertices=n)
        self.G = data.G
        self.prob = VehicleRoutingProblem(self.G,
                                          load_capacity=data.max_load,
                                          time_windows=True)
        self.prob.solve(cspy=False)
        best_value_lp = self.prob.best_value
        self.prob.solve(cspy=True)
        best_value_cspy = self.prob.best_value
        assert int(best_value_lp) == int(best_value_cspy)
