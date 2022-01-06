Using `VRPy`
============

In order to use the VRPy package, first, one has to create a directed graph which represents the underlying network.

To do so, we make use of the well-known `NetworkX` package, with the following input requirements:

 - Input graphs must be of type :class:`networkx.DiGraph`;
 - Input graphs must have a single `Source` and `Sink` nodes with no incoming or outgoing edges respectively;
 - There must be at least one path from `Source` to `Sink`;
 - Edges in the input graph must have a ``cost`` attribute (of type :class:`float`).


For example the following simple network fulfills the requirements listed above:

.. code-block:: python

	>>> from networkx import DiGraph
	>>> G = DiGraph()
	>>> G.add_edge("Source", 1, cost=1)
	>>> G.add_edge("Source", 2, cost=2)
	>>> G.add_edge(1, "Sink", cost=0)
	>>> G.add_edge(2, "Sink", cost=2)
	>>> G.add_edge(1, 2, cost=1)
	>>> G.add_edge(2, 1, cost=1)
	
The customer demands are set as ``demand`` attributes (of type :class:`float`) on each node:

.. code-block:: python

	>>> G.nodes[1]["demand"] = 5
	>>> G.nodes[2]["demand"] = 4
		
To solve your routing problem, create a :class:`VehicleRoutingProblem` instance, specify the problem constraints (e.g., the ``load_capacity`` of each truck), and call ``solve``.

.. code-block:: python

    >>> from vrpy import VehicleRoutingProblem
    >>> prob = VehicleRoutingProblem(G, load_capacity=10)
    >>> prob.solve()

Once the problem is solved, we can query useful attributes as:

.. code-block:: python

    >>> prob.best_value
    3
    >>> prob.best_routes
    {1: ["Source", 2, 1, "Sink"]}
    >>> prob.best_routes_load
    {1: 9}

``prob.best_value`` is the overall cost of the solution, ``prob.best_routes`` is a `dict` object where keys represent the route ID, while the values are
the corresponding path from `Source` to `Sink`. And ``prob.best_routes_load`` is a `dict` object where the same keys point to the accumulated load on the
vehicle.


Different options and constraints are detailed in the :ref:`vrp` section, 
and other attributes can be queried depending on the nature of the VRP (see section :ref:`api`).


