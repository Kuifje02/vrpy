Vehicle Routing Problems
========================

The `vrpy` package can solve the following VRP variants.

Capacitated Vehicle Routing Problem (CVRP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, the total load on each vehicle is cannot exceed the vehicle's capacity. 

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
	
Other resources can also be considered :
	- maximum duration per trip (each edge must also have a time attribute); 
	- maximum amount of customers that are visited.  
	
.. code-block:: python

	>>> G.edges["Source",1]["time"]=5
	>>> G.edges["Source",2]["time"]=4
	>>> G.edges[1,2]["time"]=2
	>>> G.edges[1,"Sink"]["time"]=6
	>>> G.edges[2,"Sink"]["time"]=1
	>>> prob.duration = 9
	>>> prob.num_stops = 1
	>>> prob.solve()
	
	
Note that wether the problem is a distribution or a collection problem does not matter. Both are modelled identically.

Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Time windows can be taken into account by setting lower and upper attributes on each node. Following the above example:

.. code-block:: python

	>>> G.nodes[1]["lower"] = 0
	>>> G.nodes[1]["upper"] = 10
	>>> G.nodes[2]["lower"] = 5
	>>> G.nodes[2]["upper"] = 9
	>>> prob.time_windows = True
	>>> prob.solve()


Capacitated Vehicle Routing Problem with Simultaneous Distribution and Collection (CVRPSDC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this variant, when a customer is visited, two operations can be done simultaneously. Some good is delivered, and some waste material is picked-up. 
Following the above example:

.. code-block:: python

	>>> G.nodes[1]["collect"] = 2
	>>> G.nodes[2]["collect"] = 1
	>>> prob.distribution_collection = True
	>>> prob.solve()
	
Dropping visits
~~~~~~~~~~~~~~~