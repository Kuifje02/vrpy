from networkx import DiGraph
import sys

sys.path.append("../")
sys.path.append("../vrpy/")
from vrpy.main import VehicleRoutingProblem

from examples.Solomon import DataSet


class TestsSolomon:
    def setup(self):
        """
        Solomon instance c101, 25 first nodes only including depot
        """
        self.data = DataSet(
            path="../examples/data/", instance_name="c101.txt", n_vertices=25
        )
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

    # These tests take too long for now, I am temporarily commenting them
    """
    def test_subproblem_lp(self):
        self.data.solve(num_stops=4)
        assert self.data.best_value == 553.4009812212076

    def test_subproblem_cspy(self):
        self.data.solve(num_stops=4, cspy=True)
        assert self.data.best_value == 553.4009812212076
    """
