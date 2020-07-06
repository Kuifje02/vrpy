import sys

sys.path.append("../")
from examples.benchmarks.cvrptw_solomon import DataSet


class TestsSolomon:
    def setup(self):
        """
        Solomon instance c101, 25 first nodes only including depot
        """
        self.data = DataSet(path="examples/benchmarks/data/",
                            instance_name="c101.txt",
                            n_vertices=25)
        self.G = self.data.G
        self.n_vertices = 25
        self.initial_routes = [
            ["Source", 13, 17, 18, 19, 15, 16, 14, 12, 1, "Sink"],
            ["Source", 20, 24, 23, 22, 21, "Sink"],
            ["Source", 5, 3, 7, 8, 10, 11, 6, 4, 2, "Sink"],
            ["Source", 9, "Sink"],
        ]

    def test_setup_instance_name(self):
        assert self.G.graph["name"] == "c101." + str(self.n_vertices)

    def test_setup_vehicle_capacity(self):
        assert self.G.graph["vehicle_capacity"] == 200

    def test_setup_nodes(self):
        # extra node for the Sink
        assert len(self.G.nodes()) == self.n_vertices + 1

    def test_setup_edges(self):
        assert len(
            self.G.edges()) == self.n_vertices * (self.n_vertices - 1) + 1

    def test_subproblem_lp(self):
        # benchmark result
        # e.g., in Feillet et al. (2004)
        self.data.solve(initial_routes=self.initial_routes)
        assert round(self.data.best_value, -1) in [190, 200]

    def test_subproblem_lp_dive(self):
        # benchmark result
        # e.g., in Feillet et al. (2004)
        self.data.solve(initial_routes=self.initial_routes, dive=True)
        assert round(self.data.best_value, -1) in [190, 200]

    def test_subproblem_cspy(self):
        self.data.solve(initial_routes=self.initial_routes,
                        cspy=True,
                        exact=True)
        assert round(self.data.best_value, -1) in [190, 200]
