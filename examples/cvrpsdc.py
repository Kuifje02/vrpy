from networkx import from_numpy_matrix, set_node_attributes, relabel_nodes, DiGraph
from numpy import array

from examples.data import DISTANCES, DEMANDS, COLLECT

from vrpy import VehicleRoutingProblem

# Transform distance matrix to DiGraph
A = array(DISTANCES, dtype=[("cost", int)])
G = from_numpy_matrix(A, create_using=DiGraph())

# Set demand and collect volumes
set_node_attributes(G, values=DEMANDS, name="demand")
set_node_attributes(G, values=COLLECT, name="collect")

# Relabel depot
G = relabel_nodes(G, {0: "Source", 17: "Sink"})

if __name__ == "__main__":

    prob = VehicleRoutingProblem(
        G,
        load_capacity=20,
        distribution_collection=True,
    )
    prob.solve()
    print(prob.best_value)
    print(prob.best_routes)
    print(prob.node_load)
    print(sum(prob.node_load[r]["Sink"] for r in prob.best_routes))
    assert prob.best_value == 5912
