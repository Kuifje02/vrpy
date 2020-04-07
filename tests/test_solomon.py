from networkx import DiGraph
import sys

sys.path.append("../")
sys.path.append("../vrpy/")
from vrpy.main import VehicleRoutingProblem

from examples.Solomon import DataSet


class TestsSolomon:
    def setup(self):
        """
        Solomon instance c101.txt., 3 first nodes only including depot
        """
        self.data = DataSet(
            path="../examples/data/", instance_name="c101.txt", n_vertices=3
        )
        self.G = self.data.G

    def test_setup_nodes(self):
        assert len(self.G.nodes()) == 4

    def test_setup_edges(self):
        assert len(self.G.edges()) == 6
