from math import sqrt


def distance(G, u, v):
    """2D Euclidian distance between two nodes.

    Args:
        G (Graph) :
        u (Node) : tail node.
        v (Node) : head node.

    Returns:
        float : Euclidian distance between u and v
    """
    delta_x = G.nodes[u]["x"] - G.nodes[v]["x"]
    delta_y = G.nodes[u]["y"] - G.nodes[v]["y"]
    return round(sqrt(delta_x**2 + delta_y**2), 0)
