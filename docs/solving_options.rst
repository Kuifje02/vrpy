Solving Options
===============

Initial routes
~~~~~~~~~~~~~~

By default, an initial solution is computed with the well known Clarke and Wright algorithm. If one already has a feasible solution at hand,
it is possible to use it as an initial solution. The solution is passed to the solver as a list of routes, where a route is a list
of nodes starting from the Source and ending at the Sink. 

.. code-block:: python

	>>> prob.solve(initial_solution = [["Source",1,"Sink"],["Source",2,"Sink"]])


Time limit
~~~~~~~~~~

The ``time_limit`` argument can be used to set a time limit, in seconds. For example, for a 1 minute time limit:

.. code-block:: python

	>>> prob.solve(time_limit=60)


Linear programming or dynamic programming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vrpy's ``solve`` method relies on a column generation procedure. At every iteration, a master problem and a sub problem are solved.
The sub problem consists in finding variables which are likely to improve the master problem's objective function. The sub problem - or 
pricing problem - can be solved either with linear programming, or with dynamic programming. 

Switching to linear programming can be done by deactivating the ``cspy`` argument when calling the ``solve`` method. 
In this case the CBC_ solver of COIN-OR is used. 

.. code-block:: python

	>>> prob.solve(cspy=False)
	
The subproblems that are solved are typically NP-hard, and using dynamic programming is typically quicker, as such algorithms run in pseudo-polynomial time.
However, solving the subproblems as MIPs may also be effective depending on the data set. Also, using commercial solvers may significantly help accelerating the procedure.
If one has CPLEX or GUROBI at hand, they can be used by setting the ``solver`` parameter to "cplex" or "gurobi".

.. code-block:: python

	>>> prob.solve(cspy=False, solver="gurobi")

.. _CBC : https://github.com/coin-or/Cbc
	
Pricing strategy
~~~~~~~~~~~~~~~~

By default, at each iteration the sub problem is solved optimally with a bidirectional dynamic programming, with the `cspy` library.

This may result in a slow convergence. To speed up the resolution, there are two ways to change this pricing strategy: 

1. By deactivating the ``exact`` argument of the ``solve`` method, `cspy` calls one of its heuristics instead of the bidirectional search algorithm. The exact method is run only once the heuristic fails to find a column with negative reduced cost.

.. code-block:: python

	>>> prob.solve(exact=False)
	
 
2. By modifying the ``pricing_strategy`` argument of the ``solve`` method to one of the following:
	- `Stops`;
	- `PrunePaths`;
	- `PruneEdges`.

.. code-block:: python

	>>> prob.solve(pricing_strategy="Stops")
	
The idea behind the `Stops` pricing strategy is to look for routes with a bounded number of stops. This bound is increased iteratively
if no route with negative reduced cost is found. 

The two other strategies, `PrunePaths` and `PruneEdges`, look for routes in a subgraph of the original graph. That is, a subset of nodes and
edges are removed to limit the search space. Both differ in the way the subgraph is created. `PruneEdges`, described for example by `Dell'Amico et al 2006`_
removes all edges :math:`(i,j)` which verify :math:`c_{ij} > \alpha \; \pi_{max},` where :math:`c_{ij}` is the edge's cost, :math:`\alpha \in ]0,1[` is parameter,
and :math:`\pi_{max}` is the largest dual value returned by the current restricted relaxed master problem. The parameter :math:`\alpha` is increased iteratively until
a route is found. As for `PrunePaths`, the idea is to look for routes in the subgraph induced by the :math:`k` shortest paths from the `Source` to the `Sink` (without any resource constraints), 
where :math:`k` is a parameter that increases iteratively. 

For each of these heuristic pricing strategies, if a route with negative reduced cost is found, it is fed to the master problem. Otherwise,
the sub problem is solved exactly. Also, note that these strategies can be combined: for example, it is possible to solve the subproblem heuristically with 
`cspy` (option 1), with a bounded number of stops (option 2). 

 .. _Dell'Amico et al 2006: https://pubsonline.informs.org/doi/10.1287/trsc.1050.0118
 
.. math::

    a_1 x_1 + a_2 x_2 + a_3 x_3 + ... a_n x_n \{<= , =, >=\} b 
