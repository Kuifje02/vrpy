from benchmarks.solomon_dataset import SolomonDataSet

from vrpy import VehicleRoutingProblem


class TestsSolomon:
    def setup(self):
        """
        Solomon instance c101, 25 first nodes only including depot
        """
        data = SolomonDataSet(
            path="benchmarks/data/cvrptw/", instance_name="C101.txt", n_vertices=25
        )
        self.G = data.G
        self.n_vertices = 25
        self.prob = VehicleRoutingProblem(
            self.G, load_capacity=data.max_load, time_windows=True
        )
        initial_routes = [
            ["Source", 13, 17, 18, 19, 15, 16, 14, 12, 1, "Sink"],
            ["Source", 20, 24, 23, 22, 21, "Sink"],
            ["Source", 5, 3, 7, 8, 10, 11, 6, 4, 2, "Sink"],
            ["Source", 9, "Sink"],
        ]
        # Set repeating solver arguments
        self.solver_args = {
            "pricing_strategy": "BestPaths",
            "initial_routes": initial_routes,
        }

    def test_setup_instance_name(self):
        assert self.G.graph["name"] == "C101." + str(self.n_vertices)

    def test_setup_vehicle_capacity(self):
        assert self.G.graph["vehicle_capacity"] == 200

    def test_setup_nodes(self):
        # extra node for the Sink
        assert len(self.G.nodes()) == self.n_vertices + 1

    def test_setup_edges(self):
        assert len(self.G.edges()) == self.n_vertices * (self.n_vertices - 1) + 1

    def test_subproblem_lp(self):
        # benchmark result
        # e.g., in Feillet et al. (2004)
        self.prob.solve(**self.solver_args, cspy=False)
        assert round(self.prob.best_value, -1) in [190, 200]
        self.prob.check_arrival_time()
        self.prob.check_departure_time()

    def test_subproblem_cspy(self):
        self.prob.solve(**self.solver_args, cspy=True)
        assert round(self.prob.best_value, -1) in [190, 200]
        self.prob.check_arrival_time()
        self.prob.check_departure_time()
