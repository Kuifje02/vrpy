.. _options:

Solving Options
===============

Setting initial routes for a search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, an initial solution is computed with the well known Clarke and Wright algorithm :cite:`clarke1964scheduling`. If one already has a feasible solution at hand,
it is possible to use it as an initial solution for the search of a potential better configuration. The solution is passed to the solver as a list of routes, where a route is a list
of nodes starting from the *Source* and ending at the *Sink*. 

.. code-block:: python

	>>> prob.solve(initial_solution = [["Source",1,"Sink"],["Source",2,"Sink"]])
	
Returning solution from initial heuristic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to return the solution found by the Clarke and Wright algorithm by setting the ``heuristic_only`` argument to *True*.
	
.. code-block:: python

	>>> prob.solve(heuristic_only=True)
	
Note that this only possible with capacity and/or resource constraints.
	
Locking routes
~~~~~~~~~~~~~~

It is possible to constrain the problem with partial routes if preassignments are known. There are two possibilites : either a complete route is known, 
and it should not be optimized, either only a partial route is known, and it may be extended. Such routes are given to the solver
with the ``preassignments`` argument. A route with `Source` and `Sink` nodes is considered complete and is locked. Otherwise, the solver will extend it if it yields savings.

In the following example, one route must start with customer :math:`1`, one route must contain edge :math:`(4,5)`, and one complete route,
`Source-2-3-Sink`, is locked.

.. code-block:: python

	>>> prob.solve(preassignments = [["Source",1],[4,5],["Source",2,3,"Sink"]])


Setting a time limit
~~~~~~~~~~~~~~~~~~~~

The ``time_limit`` argument can be used to set a time limit, in seconds. 
The solver will return the best solution found after the time limit has elapsed.

For example, for a one minute time limit:

.. code-block:: python

	>>> prob.solve(time_limit=60)


Linear programming or dynamic programming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`VRPy`'s ``solve`` method relies on a column generation procedure. At every iteration, a master problem and a sub problem are solved.
The sub problem consists in finding variables which are likely to improve the master problem's objective function. 
See section :ref:`colgen` for more details.

The sub problem - or pricing problem - can be solved either with linear programming, or with dynamic programming. Switching to linear 
programming can be done by deactivating the ``cspy`` argument when calling the ``solve`` method. 
In this case the CBC_ :cite:`forrest2018coin` solver of COIN-OR is used by default. 

.. code-block:: python

	>>> prob.solve(cspy=False)
	
The sub problems that are solved are typically computationally intractable, and using dynamic programming is typically quicker, as such algorithms run in pseudo-polynomial time.
However, solving the sub problems as MIPs may also be effective depending on the data set. Also, using commercial solvers may significantly help accelerating the procedure.
If one has CPLEX or GUROBI at hand, they can be used by setting the ``solver`` parameter to "cplex" or "gurobi".

.. code-block:: python

	>>> prob.solve(cspy=False, solver="gurobi")

.. _CBC : https://github.com/coin-or/Cbc
	
Pricing strategy
~~~~~~~~~~~~~~~~

In theory, at each iteration, the sub problem is solved optimally. VRPy does so with a bidirectional labeling algorithm with dynamic halfway point :cite:`tilk2017asymmetry` from the `cspy` library.

This may result in a slow convergence. To speed up the resolution, there are two ways to change this pricing strategy: 

1. By deactivating the ``exact`` argument of the ``solve`` method, `cspy` calls one of its heuristics instead of the bidirectional search algorithm. The exact method is run only once the heuristic fails to find a column with negative reduced cost.

.. code-block:: python

	>>> prob.solve(exact=False)
	
 
2. By modifying the ``pricing_strategy`` argument of the ``solve`` method to one of the following:

	- `BestEdges1`,
	- `BestEdges2`,
	- `BestPaths`,
	- `Hyper`
	

.. code-block:: python

	>>> prob.solve(pricing_strategy="BestEdges1")
	
`BestEdges1`, described for example in :cite:`dell2006branch`, is a sparsification strategy: a subset of nodes and
edges are removed to limit the search space. The subgraph is created as follows: all edges :math:`(i,j)` which verify :math:`c_{ij} > \alpha \; \pi_{max}` are discarded, where :math:`c_{ij}` is the edge's cost, :math:`\alpha \in ]0,1[` is parameter,
and :math:`\pi_{max}` is the largest dual value returned by the current restricted relaxed master problem. The parameter :math:`\alpha` is increased iteratively until
a route is found. `BestEdges2` is another sparsification strategy, described for example in :cite:`santini2018branch`. The :math:`\beta` edges with highest reduced cost are discarded, where :math:`\beta` is a parameter that is increased iteratively.
As for `BestPaths`, the idea is to look for routes in the subgraph induced by the :math:`k` shortest paths from the Source to the Sink (without any resource constraints),
where :math:`k` is a parameter that is increased iteratively.

Additionally, we have an experimental feature that uses Hyper-Heuristics for the dynamic selection of pricing strategies. 
The approach ranks the best pricing strategies as the algorithm is running and chooses according to selection functions based on :cite:`sabar2015math,ferreira2017multi`. 
The selection criteria has been modified to include a combination of runtime, objective improvement, and currently active columns in the restricted master. Adaptive parameter settings found in :cite:`drake2012improved` is used to balance exploration and exploitation under stagnation. The main advantage is that selection is done as the programme runs, and is therefore more flexible compared to a predefined pricing strategy.

For each of these heuristic pricing strategies, if a route with negative reduced cost is found, it is fed to the master problem. Otherwise,
the sub problem is solved exactly. 

The default pricing strategy is `BestEdges1`, with ``exact=True`` (i.e., with the bidirectional labeling algorithm).

A greedy randomized heuristic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the CVRP, or the CVRP with resource constraints, one can activate the option of running a greedy randomized heuristic before pricing:

.. code-block:: python

	>>> prob.solve(greedy="True")

This algorithm, described in :cite:`santini2018branch`, generates a path starting at the *Source* node and then randomly selects an edge among the :math:`\gamma` outgoing edges
of least reduced cost that do not close a cycle and that meet operational constraints (:math:`\gamma` is a parameter).
This is repeated until the *Sink* node is reached . The same procedure is applied backwards, starting from the *Sink* and ending at the *Source*, and is run
:math:`20` times. All paths with negative reduced cost are added to the pool of columns.
