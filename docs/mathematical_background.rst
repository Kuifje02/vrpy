.. _colgen:

Mathematical Background
=======================


A column generation approach
----------------------------

*VRPy* solves vehicle routing problems with a column generation approach. The term `column generation` refers to the fact 
that iteratively, routes (or `columns`) are `generated` with a pricing problem, and fed to a master problem which selects the best routes among
a pool such that each vertex is serviced exactly once. The linear formulations of these problems are detailed hereafter.  
	
Master Problem
**************
Let :math:`G=(V,A)` be a graph where :math:`V` denotes the set of nodes that have to be visited, and :math:`A` the set of edges of the network. 
Let :math:`\Omega` be the set of feasible routes. 
Let :math:`\lambda_r` be a binary variable that takes value :math:`1` if and only if route :math:`r \in \Omega` with cost :math:`c_r` is selected. 
The master problem reads as follows:


.. math:: 

	\min \; \sum_{r \in \Omega} c_r \lambda_r

subject to set covering constraints:

.. math:: 

	\sum_{r \in \Omega \mid v \in r} \lambda_r &= 1 \quad &\forall v \in V\quad &(1)

	\lambda_r &\in \{ 0,1\} \quad &\forall r \in \Omega \quad &(2)

   

When using a column generation procedure, integrity constraints :math:`(2)` are relaxed (such that :math:`0 \le \lambda_r \le 1`), and only a subset of :math:`\Omega` is used. 
This subset is generated dynamically with the following sub problem.


Pricing problem
***************

Let :math:`\pi_v` denote the dual variable associated with constraints :math:`(1)`. The marginal cost of a variable (or column) :math:`\lambda_r` is given by:

.. math:: 

	\hat{c}_r = c_r - \sum_{v \in V\mid v \in r} \pi_v

Therefore, if :math:`x_{uv}` is a binary variable that takes value :math:`1` if and only if edge :math:`(u,v)` is used, 
*assuming there are no negative cost sub cycles*, one can formulate the problem of finding a route with negative marginal cost as follows :
 
.. math:: 

	\min \quad   \sum_{(u,v)\in A}c_{uv}x_{uv} -\sum_{u\mid (u,v) \in A}\pi_u x_{uv}

subject to flow balance constraints :

.. math::  

    \sum_{u\mid (u,v) \in A} x_{uv} &=  \sum_{u\mid (v,u) \in A} x_{uv}\quad &\forall v \in V \label{eq3}
	
    x_{uv} &\in \{ 0,1\} \quad &\forall (u,v) \in A \label{eq4}


In other words, the sub problem is a shortest elementary path problem, and additional constraints (such as capacities, time) 
give rise to a shortest path problem with *resource constraints*, hence the interest of using the *cspy* library.

If there are negative cost cycles (which typically happens), the above formulation requires additional constraints
to enforce path elementarity, and the problem becomes computationally intractable.
Linear formulations are then impractical, and algorithms such as the ones available in *cspy* become very handy.


Does VRPy return an optimal solution?
-------------------------------------

*VRPy* does not necessarily return an optimal solution (even with no time limit). Indeed, once the pricing problems fails to find
a route with negative marginal cost, the master problem is solved as a MIP. This *price-and-branch* strategy does not guarantee optimality. Note however that it
can be shown :cite:`bramel1997solving` that asymptotically, the relative error goes to zero as the number of customers increases.   
To guarantee that an optimal solution is returned, the column generation procedure should be embedded in a branch-and-bound scheme (*branch-and-price*). This
is part of the future work listed below.

TO DO
-----

- Embed the solving procedure in a branch-and-bound scheme:

  - branch-and-price (exact)
  - diving (heuristic)
- Implement heuristics for initial solutions.
- More acceleration strategies:

  - other heuristic pricing strategies
  - switch to other LP modeling library (?)
  - improve stabilization
  - ...
- Include more VRP variants:

  - pickup and delivery with cspy
  - ...


