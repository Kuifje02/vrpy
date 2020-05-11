.. _vrp:

Vehicle Routing Problems
========================

The `vrpy` package can solve the following VRP variants.


Capacitated Vehicle Routing Problem (CVRP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the capacitated vehicle routing problem (CVRP), a fleet of delivery vehicles with uniform capacity must serve customers with known demand for a single commodity.
The vehicles start and end their routes at a common depot and each customer must be served by exactly one vehicle.
The objective is to assign a sequence of customers to each truck of the fleet, minimizing the total distance traveled, such that all customers are served and the total demand served by each truck does not exceed its capacity. 

.. code-block:: python

	>>> from networkx import DiGraph
	>>> G = DiGraph()
	>>> G.add_edge("Source",1,cost=1)
	>>> G.add_edge("Source",2,cost=2)
	>>> G.add_edge(1,"Sink",cost=0)
	>>> G.add_edge(2,"Sink",cost=2)
	>>> G.add_edge(1,2,cost=1)
	>>> G.nodes[1]["demand"]=2
	>>> G.nodes[2]["demand"]=3
	>>> from vrpy.main import VehicleRoutingProblem
	>>> prob = VehicleRoutingProblem(G,load_capacity=10)
	>>> prob.solve()
	
Note that whether the problem is a distribution or a collection problem does not matter. Both are modelled identically.

	
CVRP with resource constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
Other resources can also be considered :
	- maximum duration per trip; 
	- maximum amount of customers that are visited.  

Taking into account duration constraints requires setting ``time`` attributes on each edge, and setting
the ``duration`` attribute to the maximum amount of time per vehicle.

Following the above example:

.. code-block:: python

	>>> G.edges["Source",1]["time"]=5
	>>> G.edges["Source",2]["time"]=4
	>>> G.edges[1,2]["time"]=2
	>>> G.edges[1,"Sink"]["time"]=6
	>>> G.edges[2,"Sink"]["time"]=1
	>>> prob.duration = 9
	>>> prob.solve()
	
Similarly, imposing a maximum number of customers per trip is done by setting the ``num_stops`` attribute to the desired value.

.. code-block:: python

	>>> prob.num_stops = 1
	

CVRP with Time Windows (CVRPTW)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, deliveries must take place during a given time-window, which can be different for each customer.

Such constraints can be taken into account by setting ``lower`` and ``upper`` attributes on each node, and by activating the
``time_windows`` attribute to ``True.``

Following the above example:

.. code-block:: python

	>>> G.nodes[1]["lower"] = 0
	>>> G.nodes[1]["upper"] = 10
	>>> G.nodes[2]["lower"] = 5
	>>> G.nodes[2]["upper"] = 9
	>>> prob.time_windows = True
	>>> prob.solve()


CVRP with Simultaneous Distribution and Collection (CVRPSDC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, when a customer is visited, two operations are done simultaneously. Some good is delivered, and some waste material is picked-up. 
The amount that is picked-up is set with the ``collect`` attribute, on each node, and the ``distribution_collection`` attribute is set to ``True.``

Following the above example:

.. code-block:: python

	>>> G.nodes[1]["collect"] = 2
	>>> G.nodes[2]["collect"] = 1
	>>> prob.distribution_collection = True
	>>> prob.solve()
	
CVRP with Pickup and Deliveries 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the pickup-and-delivery problem, each demand is made of a pickup node and a delivery node.
Each pickup/delivery pair (or request) must be assigned to the same tour, and within this tour, the pickup node must be 
visited prior to the delivery node (as an item that is yet to be picked up cannot be delivered).

For every delivery node, the ``request`` attribute is set to the name of the pickup node. Also, the ``pickup_delivery`` attribute
is set to ``True``.

.. code-block:: python

	>>> G.nodes[2]["request"] = 1
	>>> prob.pickup_delivery = True
	>>> prob.solve(cspy=False)

.. note:: This variant has to be solved with the ``cspy`` attribute set to False. 

Dropping visits
~~~~~~~~~~~~~~~

In this variant, we consider the case where customers can be dropped, at the cost of a penalty. 
For example, if you are solving a CVRP for which the optimal solution yields a number of vehicles that is 
greater than your fleet, it may be interesting to decide which visits to drop in order to meet capacity constraints
with your given fleet. This may happen if for example, the total demand at all locations exceeds the total capacity of the fleet.

To do so, we set the ``drop_penalty`` attribute to an integer value that the solver will add to the total distance traveled
each time a node is dropped.

.. code-block:: python

	>>> prob.drop_penalty = 1000
	
Other VRPs
~~~~~~~~~~

Coming soon:

- Periodic CVRP
- CVRP with multiple depots
- CVRP with heterogeneous fleet 

