import sys
from networkx import DiGraph
from pytest import raises

sys.path.append("../../vrpy/")
from vrpy import VehicleRoutingProblem


class TestsToy:
    def setup(self):
        """
        Creates a toy graph.
        """
        self.G = DiGraph()
        for v in [1, 2, 3, 4, 5]:
            self.G.add_edge("Source", v, cost=10, time=20)
            self.G.add_edge(v, "Sink", cost=10, time=20)
            self.G.nodes[v]["demand"] = 5
            self.G.nodes[v]["upper"] = 100
            self.G.nodes[v]["lower"] = 5
            self.G.nodes[v]["service_time"] = 1
        self.G.nodes[2]["upper"] = 20
        self.G.nodes["Sink"]["upper"] = 100
        self.G.nodes["Source"]["upper"] = 100
        self.G.add_edge(1, 2, cost=10, time=20)
        self.G.add_edge(2, 3, cost=10, time=20)
        self.G.add_edge(3, 4, cost=15, time=20)
        self.G.add_edge(4, 5, cost=10, time=25)

    #################
    # subsolve cspy #
    #################

    def test_cspy_stops(self):
        """Tests column generation procedure on toy graph with stop constraints"""
        prob = VehicleRoutingProblem(self.G, num_stops=3)
        prob.solve()
        assert prob.best_value == 70
        assert prob.best_routes[1] in [
            ["Source", 1, 2, 3, "Sink"],
            ["Source", 4, 5, "Sink"],
        ]
        assert set(prob.best_routes_cost.values()) == {30, 40}
        prob.solve(exact=False)
        assert prob.best_value == 70

    def test_cspy_stops_capacity(self):
        """Tests column generation procedure on toy graph
           with stop and capacity constraints
        """
        prob = VehicleRoutingProblem(self.G, num_stops=3, load_capacity=10)
        prob.solve()
        assert prob.best_value == 80
        assert set(prob.best_routes_load.values()) == {5, 10}

    def test_cspy_stops_capacity_duration(self):
        """Tests column generation procedure on toy graph
           with stop, capacity and duration constraints
        """
        prob = VehicleRoutingProblem(self.G, num_stops=3, load_capacity=10, duration=62)
        prob.solve(exact=False)
        assert prob.best_value == 85
        assert set(prob.best_routes_duration.values()) == {41, 62}
        assert prob.node_load[1]["Sink"] in [5, 10]

    def test_cspy_stops_time_windows(self):
        """Tests column generation procedure on toy graph
           with stop, capacity and time_window constraints
        """
        prob = VehicleRoutingProblem(self.G, num_stops=3, time_windows=True,)
        prob.solve()
        assert prob.best_value == 80
        assert prob.departure_time[1]["Source"] == 0
        assert prob.arrival_time[1]["Sink"] in [41, 62]

    ###############
    # subsolve lp #
    ###############

    def test_LP_stops(self):
        """Tests column generation procedure on toy graph with stop constraints"""
        prob = VehicleRoutingProblem(self.G, num_stops=3)
        prob.solve(cspy=False)
        assert prob.best_value == 70
        prob.solve(cspy=False, pricing_strategy="BestEdges1")
        assert prob.best_value == 70

    def test_LP_stops_capacity(self):
        """Tests column generation procedure on toy graph"""
        prob = VehicleRoutingProblem(self.G, num_stops=3, load_capacity=10)
        prob.solve(cspy=False)
        assert prob.best_value == 80

    def test_LP_stops_capacity_duration(self):
        """Tests column generation procedure on toy graph"""
        prob = VehicleRoutingProblem(
            self.G, num_stops=3, load_capacity=10, duration=62,
        )
        prob.solve(cspy=False)
        assert prob.best_value == 85

    def test_LP_stops_time_windows(self):
        """Tests column generation procedure on toy graph"""
        prob = VehicleRoutingProblem(self.G, num_stops=3, time_windows=True,)
        prob.solve(cspy=False)
        assert prob.best_value == 80

    def test_LP_stops_elementarity(self):
        """Tests column generation procedure on toy graph"""
        self.G.add_edge(2, 1, cost=2)
        prob = VehicleRoutingProblem(self.G, num_stops=3,)
        prob.solve(cspy=False)
        assert prob.best_value == 67

    #########
    # other #
    #########

    def test_all(self):
        prob = VehicleRoutingProblem(
            self.G, num_stops=3, time_windows=True, duration=63, load_capacity=10
        )
        prob.solve(cspy=False)
        lp_best = prob.best_value
        prob.solve(cspy=True)
        cspy_best = prob.best_value
        assert int(lp_best) == int(cspy_best)

    def test_initial_solution(self):
        prob = VehicleRoutingProblem(self.G, num_stops=4)
        routes = [
            ["Source", 1, "Sink"],
            ["Source", 2, 3, "Sink"],
            ["Source", 4, 5, "Sink"],
        ]

        prob.solve(initial_routes=routes, cspy=False)
        assert prob.best_value == 70

    def test_knapsack(self):
        self.G.nodes["Source"]["demand"] = 0
        self.G.nodes["Sink"]["demand"] = 0
        prob = VehicleRoutingProblem(self.G, load_capacity=10)
        prob._get_num_stops_upper_bound(10)
        assert prob.num_stops == 4

    def test_pricing_strategies(self):
        prob = VehicleRoutingProblem(self.G, num_stops=4)
        sol = []
        for strategy in ["Exact", "BestPaths", "BestEdges1", "BestEdges2"]:
            prob.solve(pricing_strategy=strategy)
            sol.append(prob.best_value)
        assert len(set(sol)) == 1

    def test_lock(self):
        routes = [["Source", 3, "Sink"]]
        prob = VehicleRoutingProblem(self.G, num_stops=4)
        prob.solve(preassignments=routes)
        assert prob.best_value == 80

    def test_partial_lock(self):
        routes = [["Source", 3]]
        prob = VehicleRoutingProblem(self.G, num_stops=4)
        prob.solve(preassignments=routes)
        assert prob.best_value == 75

    def test_extend_preassignment(self):
        routes = [[2, 3]]
        prob = VehicleRoutingProblem(self.G, num_stops=4)
        prob.solve(preassignments=routes)
        assert prob.best_value == 70

    def test_pick_up_delivery(self):
        self.G.nodes[2]["request"] = 5
        self.G.nodes[2]["demand"] = 10
        self.G.nodes[3]["demand"] = 10
        self.G.nodes[3]["request"] = 4
        self.G.nodes[4]["demand"] = -10
        self.G.nodes[5]["demand"] = -10
        self.G.add_edge(2, 5, cost=10)
        self.G.remove_node(1)
        prob = VehicleRoutingProblem(self.G, load_capacity=15, pickup_delivery=True,)
        prob.solve(pricing_strategy="Exact", cspy=False)
        assert prob.best_value == 65

    def test_distribution_collection(self):
        self.G.nodes[1]["collect"] = 12
        self.G.nodes[4]["collect"] = 1
        prob = VehicleRoutingProblem(
            self.G, load_capacity=15, distribution_collection=True,
        )
        prob.solve(cspy=False)
        lp_sol = prob.best_value
        prob.solve(cspy=True)
        cspy_sol = prob.best_value
        assert lp_sol == cspy_sol
        assert lp_sol == 80

    def test_fixed_cost(self):
        prob = VehicleRoutingProblem(self.G, num_stops=3, fixed_cost=100)
        prob.solve()
        assert prob.best_value == 70 + 200
        assert set(prob.best_routes_cost.values()) == {30 + 100, 40 + 100}

    def test_drop_nodes(self):
        prob = VehicleRoutingProblem(
            self.G, num_stops=3, num_vehicles=1, drop_penalty=100
        )
        prob.solve()
        assert prob.best_value == 240
        assert prob.best_routes == {1: ["Source", 1, 2, 3, "Sink"]}

    def test_periodic(self):
        self.G.nodes[2]["frequency"] = 2
        prob = VehicleRoutingProblem(self.G, num_stops=2, periodic=2)
        prob.solve()
        assert prob.best_value == 90
        frequency = 0
        for r in prob.best_routes:
            if 2 in prob.best_routes[r]:
                frequency += 1
        assert frequency == 2
        assert prob.schedule[0] in [[1], [1, 2]]

    def test_mixed_fleet(self):
        for (i, j) in self.G.edges():
            self.G.edges[i, j]["cost"] = 2 * [self.G.edges[i, j]["cost"]]
        prob = VehicleRoutingProblem(
            self.G,
            load_capacity=[10, 15],
            fixed_cost=[10, 0],
            num_vehicles=[5, 1],
            mixed_fleet=True,
        )
        prob.solve()
        assert prob.best_value == 80
        assert set(prob.best_routes_type.values()) == {0, 1}

    def test_time_limit(self):
        prob = VehicleRoutingProblem(self.G, num_stops=3)
        prob.solve(cspy=False, time_limit=0.01)
        assert prob.best_value == 70


"""
    def test_dive(self):
        # TODO
        pass
"""
