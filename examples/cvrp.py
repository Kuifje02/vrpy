from networkx import from_numpy_matrix, set_node_attributes, relabel_nodes, DiGraph
from numpy import array
from examples.data import DISTANCES, DEMANDS

from vrpy import VehicleRoutingProblem

# Transform distance matrix to DiGraph
A = array(DISTANCES, dtype=[("cost", int)])
G = from_numpy_matrix(A, create_using=DiGraph())

# Set demands
set_node_attributes(G, values=DEMANDS, name="demand")

# Relabel depot
G = relabel_nodes(G, {0: "Source", 17: "Sink"})

if __name__ == "__main__":

    prob = VehicleRoutingProblem(G, load_capacity=15)
    prob.solve()
    print(prob.best_value)
    print(prob.best_routes)
    assert prob.best_value == 6208
