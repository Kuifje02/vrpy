from networkx import DiGraph, add_path, shortest_path

import sys

sys.path.append("../../vrpy/")
from vrpy.clarke_wright import ClarkeWright


def test_cw():
    G = DiGraph()

    G.add_node(2, demand=4)
    G.add_node(3, demand=6)
    G.add_node(4, demand=5)
    G.add_node(5, demand=4)
    G.add_node(6, demand=7)
    G.add_node(7, demand=3)
    G.add_node(8, demand=5)
    G.add_node(9, demand=4)
    G.add_node(10, demand=4)

    G.add_edge("Source", 2, cost=25)
    G.add_edge("Source", 3, cost=43)
    G.add_edge("Source", 4, cost=57)
    G.add_edge("Source", 5, cost=43)
    G.add_edge("Source", 6, cost=61)
    G.add_edge("Source", 7, cost=29)
    G.add_edge("Source", 8, cost=41)
    G.add_edge("Source", 9, cost=48)
    G.add_edge("Source", 10, cost=71)

    G.add_edge(2, "Sink", cost=25)
    G.add_edge(3, "Sink", cost=43)
    G.add_edge(4, "Sink", cost=57)
    G.add_edge(5, "Sink", cost=43)
    G.add_edge(6, "Sink", cost=61)
    G.add_edge(7, "Sink", cost=29)
    G.add_edge(8, "Sink", cost=41)
    G.add_edge(9, "Sink", cost=48)
    G.add_edge(10, "Sink", cost=71)

    G.add_edge(3, 2, cost=29)
    G.add_edge(4, 2, cost=34)
    G.add_edge(5, 2, cost=43)
    G.add_edge(6, 2, cost=68)
    G.add_edge(7, 2, cost=49)
    G.add_edge(8, 2, cost=66)
    G.add_edge(9, 2, cost=72)
    G.add_edge(10, 2, cost=91)

    G.add_edge(4, 3, cost=52)
    G.add_edge(5, 3, cost=72)
    G.add_edge(6, 3, cost=96)
    G.add_edge(7, 3, cost=72)
    G.add_edge(8, 3, cost=81)
    G.add_edge(9, 3, cost=89)
    G.add_edge(10, 3, cost=114)

    G.add_edge(5, 4, cost=45)
    G.add_edge(6, 4, cost=71)
    G.add_edge(7, 4, cost=71)
    G.add_edge(8, 4, cost=95)
    G.add_edge(9, 4, cost=99)
    G.add_edge(10, 4, cost=108)

    G.add_edge(6, 5, cost=27)
    G.add_edge(7, 5, cost=36)
    G.add_edge(8, 5, cost=65)
    G.add_edge(9, 5, cost=65)
    G.add_edge(10, 5, cost=65)

    G.add_edge(7, 6, cost=40)
    G.add_edge(8, 6, cost=66)
    G.add_edge(9, 6, cost=62)
    G.add_edge(10, 6, cost=46)

    G.add_edge(8, 7, cost=31)
    G.add_edge(9, 7, cost=31)
    G.add_edge(10, 7, cost=43)

    G.add_edge(9, 8, cost=11)
    G.add_edge(10, 8, cost=46)

    G.add_edge(10, 9, cost=36)

    new = []
    for (i, j) in G.edges():
        if i != "Source" and j != "Sink":
            new.append((i, j))

    for (i, j) in new:
        G.add_edge(j, i, cost=G.edges[i, j]["cost"])

    for (i, j) in G.edges():
        G.edges[i, j]["time"] = 1
    for i in G.nodes():
        G.nodes[i]["service_time"] = 1

    alg = ClarkeWright(G, load_capacity=23, num_stops=None, duration=None)
    alg.run()
    assert alg.best_value == 397
