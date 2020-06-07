from networkx import from_numpy_matrix, set_node_attributes, relabel_nodes, DiGraph
from numpy import matrix
from data import DISTANCES, DEMANDS
import sys

sys.path.append("../../")
from vrpy import VehicleRoutingProblem

# Transform distance matrix to DiGraph
A = matrix(DISTANCES, dtype=[("cost", int)])
G = from_numpy_matrix(A, create_using=DiGraph())

# Set demands
set_node_attributes(G, values=DEMANDS, name="demand")

# Relabel depot
G = relabel_nodes(G, {0: "Source", 17: "Sink"})

if __name__ == "__main__":
    from time import time

    prob = VehicleRoutingProblem(G, load_capacity=15)
    start = time()
    prob.solve(cspy=False, solver="cplex")
    print(round(time() - start), "sec")
    print(prob.best_value)
    print(prob.best_routes)
