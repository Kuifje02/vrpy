import sys

sys.path.append("../")

from examples.benchmarks.mdvrp_cordeau import DataSet


class TestsCordeau:
    def setup(self):
        """
        Cordeau instance p01, 8 vertices only.
        """
        self.data = DataSet(
            path="../examples/benchmarks/data/", instance_name="p01", n_vertices=8
        )
        self.G = self.data.G

    def test_setup_instance_name(self):
        assert self.G.graph["name"] == "p01"

    def test_setup_vehicle_capacity(self):
        assert self.G.graph["vehicle_capacity"] == 80

    def test_setup_nodes(self):
        # nodes + source + sink + depots x 2
        assert len(self.G.nodes()) == 18

    def test_setup_edges(self):
        assert len(self.G.edges()) == 128

    """
    Needs some dev
    def test_subproblem_lp_with_initial_routes(self):
        # initial solution
        # ugly, needs more genericity
        ini = []
        for v in self.G.nodes():
            if "customer" in self.G.nodes[v]:
                ini.append(["Source", 51, v, str(51) + "_", "Sink"])
        self.data.solve(initial_routes=ini, cspy=False)
        assert round(self.data.best_value, 1) == 141.9
    """
