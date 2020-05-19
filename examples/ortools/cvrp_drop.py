from networkx import from_numpy_matrix, set_node_attributes, relabel_nodes, DiGraph
from numpy import matrix
from data import DISTANCES, DEMANDS_DROP
import sys

sys.path.append("../../")
sys.path.append("../../../cspy")
from vrpy import VehicleRoutingProblem

# Transform distance matrix to DiGraph
A = matrix(DISTANCES, dtype=[("cost", int)])
G = from_numpy_matrix(A, create_using=DiGraph())

# Set demands
set_node_attributes(G, values=DEMANDS_DROP, name="demand")

# Relabel depot
G = relabel_nodes(G, {0: "Source", 17: "Sink"})

if __name__ == "__main__":

    routes = [
        ["Source", 9, 14, 16, "Sink"],
        ["Source", 12, 11, 4, 3, 1, "Sink"],
        ["Source", 7, 13, "Sink"],
        ["Source", 8, 10, 2, 5, "Sink"],
    ]

    prob = VehicleRoutingProblem(G, load_capacity=15, drop_penalty=1000, num_vehicles=4)
    prob.solve(preassignments=routes, pricing_strategy="PrunePaths")
    print(prob.best_value)
    print(prob.best_routes)
    print(prob.best_routes_cost)
    print(prob.best_routes_load)
    print(prob.node_load)
