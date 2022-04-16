from networkx import (
    from_numpy_matrix,
    set_node_attributes,
    relabel_nodes,
    DiGraph,
    compose,
)
from numpy import array
import sys

sys.path.append("../vrpy/")
from vrpy import VehicleRoutingProblem
from examples.data import (
    DISTANCES,
    TRAVEL_TIMES,
    TIME_WINDOWS_LOWER,
    TIME_WINDOWS_UPPER,
    PICKUPS_DELIVERIES,
    DEMANDS,
    COLLECT,
)


class TestsOrTools:
    def setup(self):
        # Transform distance matrix to DiGraph
        A = array(DISTANCES, dtype=[("cost", int)])
        G_d = from_numpy_matrix(A, create_using=DiGraph())
        # Transform time matrix to DiGraph
        A = array(TRAVEL_TIMES, dtype=[("time", int)])
        G_t = from_numpy_matrix(A, create_using=DiGraph())
        # Merge
        G = compose(G_d, G_t)
        # Set time windows
        set_node_attributes(G, values=TIME_WINDOWS_LOWER, name="lower")
        set_node_attributes(G, values=TIME_WINDOWS_UPPER, name="upper")
        # Set demand and collect volumes
        set_node_attributes(G, values=DEMANDS, name="demand")
        set_node_attributes(G, values=COLLECT, name="collect")
        # Relabel depot
        self.G = relabel_nodes(G, {0: "Source", 17: "Sink"})
        # Define VRP
        self.prob = VehicleRoutingProblem(self.G)

    def test_cvrp_dive_lp(self):
        self.prob.load_capacity = 15
        self.prob.solve(cspy=False, pricing_strategy="BestEdges1", dive=True)
        assert int(self.prob.best_value) == 6208

    def test_cvrp_dive_cspy(self):
        self.prob.load_capacity = 15
        self.prob.solve(pricing_strategy="BestEdges1", dive=True)
        assert int(self.prob.best_value) == 6208

    def test_vrptw_dive_lp(self):
        self.prob.time_windows = True
        self.prob.solve(cspy=False, dive=True)
        assert int(self.prob.best_value) == 6528

    def test_vrptw_dive_cspy(self):
        self.prob.time_windows = True
        self.prob.solve(cspy=True, dive=True)
        assert int(self.prob.best_value) == 6528

    def test_cvrpsdc_dive_lp(self):
        self.prob.load_capacity = 15
        self.prob.distribution_collection = True
        self.prob.solve(cspy=False, pricing_strategy="BestEdges1", dive=True)
        assert int(self.prob.best_value) == 6208

    def test_cvrpsdc_dive_cspy(self):
        self.prob.load_capacity = 15
        self.prob.distribution_collection = True
        self.prob.solve(pricing_strategy="BestEdges1", dive=True)
        assert int(self.prob.best_value) == 6208

    def test_pdp_dive_lp(self):
        # Set demands and requests
        for (u, v) in PICKUPS_DELIVERIES:
            self.G.nodes[u]["request"] = v
            self.G.nodes[u]["demand"] = PICKUPS_DELIVERIES[(u, v)]
            self.G.nodes[v]["demand"] = -PICKUPS_DELIVERIES[(u, v)]
        self.prob.pickup_delivery = True
        self.prob.load_capacity = 10
        self.prob.num_stops = 6
        self.prob.solve(cspy=False, dive=True)
        sol_lp = self.prob.best_value
        assert int(sol_lp) == 5980

    def test_cvrp_lp(self):
        self.prob.load_capacity = 15
        self.prob.solve(cspy=False, pricing_strategy="BestEdges1")
        assert int(self.prob.best_value) == 6208

    def test_cvrp_cspy(self):
        self.prob.load_capacity = 15
        self.prob.solve(pricing_strategy="BestEdges1")
        assert int(self.prob.best_value) == 6208

    def test_vrptw_lp(self):
        self.prob.time_windows = True
        self.prob.solve(cspy=False)
        assert int(self.prob.best_value) == 6528

    def test_vrptw_cspy(self):
        self.prob.time_windows = True
        self.prob.solve()
        assert int(self.prob.best_value) == 6528

    def test_cvrpsdc_lp(self):
        self.prob.load_capacity = 15
        self.prob.distribution_collection = True
        self.prob.solve(cspy=False, pricing_strategy="BestEdges1")
        assert int(self.prob.best_value) == 6208

    def test_cvrpsdc_cspy(self):
        self.prob.load_capacity = 15
        self.prob.distribution_collection = True
        self.prob.solve(pricing_strategy="BestEdges1")
        assert int(self.prob.best_value) == 6208

    def test_pdp_lp(self):
        # Set demands and requests
        for (u, v) in PICKUPS_DELIVERIES:
            self.G.nodes[u]["request"] = v
            self.G.nodes[u]["demand"] = PICKUPS_DELIVERIES[(u, v)]
            self.G.nodes[v]["demand"] = -PICKUPS_DELIVERIES[(u, v)]
        self.prob.pickup_delivery = True
        self.prob.load_capacity = 10
        self.prob.num_stops = 6
        self.prob.solve(cspy=False)
        sol_lp = self.prob.best_value
        assert int(sol_lp) == 5980
