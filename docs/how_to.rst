Using `vrpy`
============

In order to use the `vrpy` package, first, one has to create a directed graph which represents the underlying network.

To do so, we make use of the well-known `networkx` package, with the following input requirements:

 - Input graphs must be of type :class:`networkx.DiGraph`;
 - Input graphs must have a single `Source` and `Sink` nodes with no incoming or outgoing edges respectively;
 - Edges in the input graph must have a ``cost`` attribute (of type :class:`int` or :class:`float`).


For example the following simple network fulfills the requirements listed above:

.. code-block:: python

	>>> from networkx import DiGraph
	>>> G = DiGraph()
	>>> G.add_edge("Source",1,cost=1)
	>>> G.add_edge("Source",2,cost=2)
	>>> G.add_edge(1,"Sink",cost=0)
	>>> G.add_edge(2,"Sink",cost=2)
	>>> G.add_edge(1,2,cost=1)
	
The customer demands are set as ``demand`` attributes (of type :class:`int` or :class:`float`) on each node:

.. code-block:: python

	>>> G.nodes[1]["demand"]=2
	>>> G.nodes[2]["demand"]=3
		
To solve your routing problem, create a :class:`VehicleRoutingProblem`, specify the problem constraints (e.g., the ``load_capacity`` of each truck), and call ``solve``.

.. code-block:: python

	>>> from vrpy.main import VehicleRoutingProblem
	>>> prob = VehicleRoutingProblem(G,load_capacity=10)
	>>> prob.solve()

Once the problem is solved, we can query useful attributes as

.. code-block:: python

	prob.best_value
	prob.best_routes

``prob.best_value`` is the overall cost of the solution, ``prob.best_routes`` is the list of routes found by the algorithm. A route is represented as a list of nodes.


Different options and constraints are detailed in the CVRP section : :ref:`cvrp`


