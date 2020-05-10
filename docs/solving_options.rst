Solving Options
===============

Initial routes
~~~~~~~~~~~~~~

By default, an initial solution is computed with the well known Clarke and Wright algorithm. If one already has a feasible solution at hand,
it is possible to use it as an initial solution. 

.. code-block:: python

	>>> prob.solve(initial_solution = [["Source",1,"Sink"],["Source",2,"Sink"]])

Customer routes
~~~~~~~~~~~~~~~

One may want to fix partial routes. 

Time limit
~~~~~~~~~~


Linear programming or dynamic programming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vrpy's ``solve`` method relies on a column generation procedure. At every iteration, a master problem and a sub problem are solved.
The sub problem consists in finding variables which are likely to improve the master problem's objective function. The sub problem - or 
pricing problem - can be solved either with linear programming, or with dynamic programming. 

By default, the sub problem is solved with bidirectional dynamic programming, with the `cspy` library. By deactivating the
``exact`` attribute of the ``solve`` method, cspy calls one of its heuristics instead of the bidirectional search algorithm.

.. code-block:: python

	>>> prob.solve(exact=False)

Switching to linear programming can be done by deactivating the cspy attribute when calling the ``solve`` method. 
In this case the CBC solver of COIN-OR is used. 

.. code-block:: python

	>>> prob.solve(cspy=False)
	
Pricing strategy
~~~~~~~~~~~~~~~~

By default, the sub problem is solved optimally at each iteration. This may result in a slow convergence. To speed up the resolution,
it is possible to use other heuristic pricing strategies, by modifying the ``pricing_strategy`` attribute of the ``solve`` method. 

If the heuristic fails to solve the sub problem, the exact method is run. 

.. code-block:: python

	>>> prob.solve(pricing_strategy="Stops")