from networkx import DiGraph
import sys

sys.path.append("../")

from vrpy.main import VehicleRoutingProblem

from examples.benchmarks.cvrptw_solomon import DataSet


class TestsSolomon:

    def setup(self):
        """
        Solomon instance c101, 25 first nodes only including depot
        """
        self.data = DataSet(path="../examples/benchmarks/data/",
                            instance_name="c101.txt",
                            n_vertices=25)
        self.G = self.data.G
        self.n_vertices = 25

    def test_setup_instance_name(self):
        assert self.G.graph["name"] == "c101." + str(self.n_vertices)

    def test_setup_vehicle_capacity(self):
        assert self.G.graph["vehicle_capacity"] == 200

    def test_setup_nodes(self):
        # extra node for the Sink
        assert len(self.G.nodes()) == self.n_vertices + 1

    def test_setup_edges(self):
        assert len(self.G.edges()) == self.n_vertices * (self.n_vertices - 1)

    def test_subproblem_lp(self):
        # benchmark result
        # e.g., in Feillet et al. (2004)
        self.data.solve()
        assert int(self.data.best_value) == 191

    def test_subproblem_cspy(self):
        self.data.solve(cspy=True, exact=True)
        assert int(self.data.best_value) == 191
