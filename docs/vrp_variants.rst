.. _vrp:

Vehicle Routing Problems
========================

The `VRPy` package can solve the following VRP variants.


Capacitated Vehicle Routing Problem (CVRP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the capacitated vehicle routing problem (CVRP), a fleet of vehicles with uniform capacity must serve customers with known demand for a single commodity.
The vehicles start and end their routes at a common depot and each customer must be served by exactly one vehicle.
The objective is to assign a sequence of customers (a route) to each truck of the fleet, minimizing the total distance traveled, 
such that all customers are served and the total demand served by each truck does not exceed its capacity. 

.. code-block:: python

	>>> from networkx import DiGraph
	>>> from vrpy import VehicleRoutingProblem
	>>> G = DiGraph()
	>>> G.add_edge("Source", 1, cost=1)
	>>> G.add_edge("Source", 2, cost=2)
	>>> G.add_edge(1, "Sink", cost=0)
	>>> G.add_edge(2, "Sink", cost=2)
	>>> G.add_edge(1, 2, cost=1)
	>>> G.nodes[1]["demand"] = 2
	>>> G.nodes[2]["demand"] = 3
	>>> prob = VehicleRoutingProblem(G, load_capacity=10)
	>>> prob.solve()
	
Note that whether the problem is a distribution or a collection problem does not matter. Both are modeled identically.

	
CVRP with resource constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
Other resources can also be considered:

	- maximum duration per trip; 
	- maximum number of customers per trip.  

Taking into account duration constraints requires setting ``time`` attributes on each edge, and setting
the ``duration`` attribute to the maximum amount of time per vehicle.

Following the above example:

.. code-block:: python

	>>> G.edges["Source",1]["time"] = 5
	>>> G.edges["Source",2]["time"] = 4
	>>> G.edges[1,2]["time"] = 2
	>>> G.edges[1,"Sink"]["time"] = 6
	>>> G.edges[2,"Sink"]["time"] = 1
	>>> prob.duration = 9
	>>> prob.solve()
	
Similarly, imposing a maximum number of customers per trip is done by setting the ``num_stops`` attribute to the desired value.

.. code-block:: python

	>>> prob.num_stops = 1
	

CVRP with Time Windows (CVRPTW)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, deliveries must take place during a given time-window, which can be different for each customer.

Such constraints can be taken into account by setting ``lower`` and ``upper`` attributes on each node, and by activating the
``time_windows`` attribute to ``True.`` Additionally, service times can be taken into account on each node by setting the ``service_time``
attribute.

Following the above example:

.. code-block:: python

	>>> G.nodes[1]["lower"] = 0
	>>> G.nodes[1]["upper"] = 10
	>>> G.nodes[2]["lower"] = 5
	>>> G.nodes[2]["upper"] = 9
	>>> G.nodes[1]["service_time"] = 1
	>>> G.nodes[2]["service_time"] = 2
	>>> prob.time_windows = True
	>>> prob.solve()
	
.. note:: 

	Waiting time is allowed upon arrival at a node. This means that if a vehicle arrives at a node before the time window's
	lower bound, the configuration remains feasible, it is considered that the driver waits before servicing the customer. 
        


CVRP with Simultaneous Distribution and Collection (CVRPSDC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, when a customer is visited, two operations are done simultaneously. Some good is delivered, and some waste material is picked-up. 
The total load must not exceed the vehicle's capacity.

The amount that is picked-up is set with the ``collect`` attribute on each node, and the ``distribution_collection`` attribute is set to ``True.``

Following the above example:

.. code-block:: python

	>>> G.nodes[1]["collect"] = 2
	>>> G.nodes[2]["collect"] = 1
	>>> prob.load_capacity = 2
	>>> prob.distribution_collection = True
	>>> prob.solve()
	
CVRP with Pickup and Deliveries (VRPPD)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the pickup-and-delivery problem, each demand is made of a pickup node and a delivery node.
Each pickup/delivery pair (or request) must be assigned to the same tour, and within this tour, the pickup node must be 
visited prior to the delivery node (as an item that is yet to be picked up cannot be delivered). 
The total load must not exceed the vehicle's capacity.

For every pickup node, the ``request`` attribute points to the name of the delivery node. Also, the ``pickup_delivery`` attribute
is set to ``True``. The amount of goods to be shipped is counted positively for the pickup node, and negatively for the delivery node.
For example, if :math:`3` units must be shipped from node :math:`1` to node :math:`2`, the ``demand`` attribute is set to :math:`3` for node :math:`1`, and :math:`-3` for node :math:`2`.

.. code-block:: python

	>>> G.nodes[1]["request"] = 2
	>>> G.nodes[1]["demand"] = 3
	>>> G.nodes[2]["demand"] = -3
	>>> prob.pickup_delivery = True
	>>> prob.load_capacity = 10
	>>> prob.solve(cspy=False)

.. note:: This variant has to be solved with the ``cspy`` attribute set to False. 

Periodic CVRP (PCVRP)
~~~~~~~~~~~~~~~~~~~~~

In the periodic CVRP, the planning period is extended over a time horizon, and customers can be serviced more than once. 
The demand is considered constant over time, and the frequencies (the number of visits) of each customer are known. 

For each node, the ``frequency`` attribute (type :class:`int`) is set, and the parameter ``periodic`` is set to the value of the considered time span (the planning period).
All nodes that have no frequency are visited exactly once. 

.. code-block:: python

	>>> G.nodes[1]["frequency"] = 2
	>>> prob.periodic = 2
	>>> prob.solve()
	
A planning of the routes can then be queried by calling ``prob.schedule,`` which returns a dictionary with keys day numbers and values the list of
route numbers scheduled this day. 
	
.. note:: 

	The PCVRP usually has additional constraints: some customers can only be serviced on specific days of the considered time span. 
	For example, over a :math:`3` day planning period, a node with frequency :math:`2` could only be visited on days :math:`1` and
	:math:`2` or :math:`2` and :math:`3` but not :math:`1` and :math:`3`. Such *combination* constraints are not taken into account by 
	*VRPy* (yet).
	
.. note::

   If the parameter ``num_vehicles`` is used, it refers to the maximum number of vehicles available per day (and not over the time span).
	
CVRP with heterogeneous fleet (HFCVRP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the CVRP with *heterogeneous fleet* (or mixed fleet), there are different types of vehicles, which can differ in capacities and costs (fixed costs
and travel costs). Typically, a vehicle with a larger capacity will be more expensive. The problem consists in finding the best combination of
vehicles to satisfy the demands while minimizing global costs. 

First, the ``cost`` attribute on each of the graph is now a *list* of costs, with as many items as vehicle types (even if costs are equal). For example,
if there are *two* types of vehicles, the following graph satisfies the input requirements:

.. code-block:: python

	>>> from networkx import DiGraph
	>>> G = DiGraph()
	>>> G.add_edge("Source", 1, cost=[1, 2])
	>>> G.add_edge("Source", 2, cost=[2, 4])
	>>> G.add_edge(1, "Sink", cost=[0, 0])
	>>> G.add_edge(2, "Sink", cost=[2, 4])
	>>> G.add_edge(1, 2, cost=[1, 2])

When defining the ``VehicleRoutingProblem``, the ``mixed_fleet`` argument is set to ``True``, and the ``load_capacity`` argument is now also of type :class:`list`,
where each item of the list is the maximum load per vehicle type. For example, if the two types of vehicles have capacities :math:`10` and :math:`15`, respectively:

.. code-block:: python

    >>> from vrpy import VehicleRoutingProblem
    >>> prob = VehicleRoutingProblem(G, mixed_fleet=True, load_capacity=[10, 15])

Note how the dimensions of ``load_capacity`` and ``cost`` are consistent: each list must have as many items as vehicle types, and the
order of the items of the ``load_capacity`` list is consistent with the order of the ``cost`` list on every edge of the graph.
  
Once the problem is solved, the type of vehicle per route can be queried with ``prob.best_routes_type``.  

	
VRP options
~~~~~~~~~~~

In this subsection are described different options which arise frequently in vehicle routing problems.

Open VRP
^^^^^^^^

The `open` VRP refers to the case where vehicles can start and/or end their trip anywhere, instead of having to leave from
the depot, and to return there after service. This is straightforward to model : setting distances (or costs) to :math:`0` on every edge outgoing from the Source 
and incoming to the Sink achieves this.

Fixed costs
^^^^^^^^^^^

Vehicles typically have a *fixed cost* which is charged no matter what the traveled distance is. This can be taken into account with the ``fixed_cost`` attribute.
For example, if the cost of using each vehicle is :math:`100`: 

.. code-block:: python

	>>> prob.fixed_cost = 100
	
.. note:: 

	If the fleet is mixed, the same logic holds for ``fixed_cost``: a list of costs is given, where each item of the list is the fixed cost per vehicle type.
	The order of the items of the list has to be consistent with the other lists (``cost`` and ``load_capacity``). See example :ref:`hfvrp`.
	
Limited fleet
^^^^^^^^^^^^^
	
It is possible to limit the size of the fleet. For example, if at most :math:`10` vehicles are available:

.. code-block:: python

	>>> prob.num_vehicles = 10
	
.. note:: 

	If the fleet is mixed, the same logic holds for ``num_vehicles``: a list of integers is given, where each item of the list is
	the number of available vehicles, per vehicle type. The order of the items of the list has to be consistent with the other
	lists (``cost``, ``load_capacity``, ``fixed_cost``).
	
And to enforce exactly ``num_vehicles`` vehicles, one can use the ``use_all_vehicles``:

.. code-block:: python

	>>> prob.use_all_vehicles = True
	
Dropping visits
^^^^^^^^^^^^^^^

Having a limited fleet may result in an infeasible problem. For example, if the total demand at all locations exceeds the total capacity of the fleet,
the problem has no feasible solution. It may then be interesting to decide which visits to drop in order to meet capacity constraints
while servicing as many customers as possible. To do so, we set the ``drop_penalty`` attribute to an integer value that the solver
will add to the total travel cost each time a node is dropped. For example, if the value of the penalty is :math:`1000`:

.. code-block:: python

	>>> prob.drop_penalty = 1000
	
This problem is sometimes referred to as the `capacitated profitable tour problem` or the `prize collecting tour problem.`

Minimizing the global time span
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to modify the objective function in order to solve a min-max problem. More specifically, the total time span can be minimized
by setting the ``minimize_global_span`` to ``True``. Of course this assumes edges have a ``time`` argument:

.. code-block:: python

	>>> prob.minimize_global_span = True
	
.. note::

   This may lead to poor computation times.
	
Other VRPs
~~~~~~~~~~

Coming soon:

- CVRP with multiple depots

