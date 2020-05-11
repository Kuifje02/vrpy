Solving Options
===============

Initial routes
~~~~~~~~~~~~~~

By default, an initial solution is computed with the well known Clarke and Wright algorithm. If one already has a feasible solution at hand,
it is possible to use it as an initial solution. The solution is passed to the solver as a list of routes, where a route is a list
of nodes starting from the Source and ending at the Sink. Also, to compute the cost of this solution, a cost function must be given to the solver,
which maps a pair of nodes to a positive value. 

For example, if each node has a pair of :math:`(x,y)` coordinates, and if you are working with the "taxi distance", such a cost function can be defined as follows:

.. code-block:: python

	def manhattan_distance(node_1, node_2):
	   Dx = abs(G.nodes[node_1]["x"]-G.nodes[node_2]["x"])
	   Dy = abs(G.nodes[node_1]["y"]-G.nodes[node_2]["y"])
	   return Dx + Dy

The problem can then be solved, with the following arguments: 

.. code-block:: python

	>>> prob.solve(initial_solution = [["Source",1,"Sink"],["Source",2,"Sink"]], edge_cost_function=manhattan_distance)



Time limit
~~~~~~~~~~

The ``time_limit`` attribute can be used to set a time limit, in seconds. For example, for a 1 minute time limit:

.. code-block:: python

	>>> prob.solve(time_limit=60)


Linear programming or dynamic programming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vrpy's ``solve`` method relies on a column generation procedure. At every iteration, a master problem and a sub problem are solved.
The sub problem consists in finding variables which are likely to improve the master problem's objective function. The sub problem - or 
pricing problem - can be solved either with linear programming, or with dynamic programming. 

Switching to linear programming can be done by deactivating the ``cspy`` attribute when calling the ``solve`` method. 
In this case the CBC solver of COIN-OR is used. 

.. code-block:: python

	>>> prob.solve(cspy=False)
	
The subproblems that are solved are typically NP-hard, and using dynamic programming is typically quicker, as such algorithms run in pseudo-polynomial time.
However, solving the subproblems as MIPs may be more effective for small data sets. 
	
Pricing strategy
~~~~~~~~~~~~~~~~

By default, at each iteration the sub problem is solved optimally with a bidirectional dynamic programming, with the `cspy` library.

This may result in a slow convergence. To speed up the resolution, there are two ways to change this pricing strategy: 

	1. By deactivating the ``exact`` attribute of the ``solve`` method, cspy calls one of its heuristics instead of the bidirectional search algorithm. The exact method is run only once the heuristic fails to find a column with negative reduced cost.

.. code-block:: python

	>>> prob.solve(exact=False)
	
 
 2. By modifying the ``pricing_strategy`` attribute of the ``solve`` method to one of the following:
	- "Stops";
	- "PrunePaths";
	- "PruneEdges".

.. code-block:: python

	>>> prob.solve(pricing_strategy="Stops")