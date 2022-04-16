from pytest import fixture
from time import time
import csv

from vrpy import VehicleRoutingProblem

from benchmarks.solomon_dataset import SolomonDataSet

params = list(range(7, 70))


@fixture(
    scope="class",
    params=params,
)
def n(request):
    print("setup once per each param", request.param)
    return request.param


REPS_LP = 1
REPS_CSPY = 10


def write_avg(n, times_cspy, iter_cspy, times_lp, iter_lp, name="cspy102fwdearly"):
    def _avg(l):
        return sum(l) / len(l)

    with open(f"benchmarks/results/{name}.csv", "a", newline="") as f:
        writer_object = csv.writer(f)
        writer_object.writerow(
            [n, _avg(times_cspy), _avg(iter_cspy), _avg(times_lp), _avg(iter_lp)]
        )
        f.close()


class TestsSolomon:
    def test_subproblem(self, n):
        data = SolomonDataSet(
            path="benchmarks/data/cvrptw/", instance_name="C101.txt", n_vertices=n
        )
        self.G = data.G
        best_values_lp = None
        lp_iter = []
        times_lp = []
        for r in range(REPS_LP):
            prob = VehicleRoutingProblem(
                self.G, load_capacity=data.max_load, time_windows=True
            )
            start = time()
            prob.solve(cspy=False)
            best_value_lp = prob.best_value
            times_lp.append(time() - start)
            lp_iter.append(prob._iteration)
            del prob
        best_values_cspy = []
        times_cspy = []
        iter_cspy = []
        for r in range(REPS_CSPY):
            prob = VehicleRoutingProblem(
                self.G, load_capacity=data.max_load, time_windows=True
            )
            start = time()
            prob.solve(cspy=True, pricing_strategy="Exact")
            times_cspy.append(time() - start)
            best_values_cspy.append(prob.best_value)
            iter_cspy.append(prob._iteration)
            prob.check_arrival_time()
            prob.check_departure_time()
            del prob
        assert all(best_value_lp == val_cspy for val_cspy in best_values_cspy)
        write_avg(n, times_cspy, iter_cspy, times_lp, lp_iter)
