.. _api:

API
===

vrpy.VehicleRoutingProblem
--------------------------

.. automodule:: vrpy.vrp
   :members:
   :inherited-members:
   

Notes
-----

The input graph must have single `Source` and `Sink` nodes with no incoming or outgoing edges respectively. 
These dummy nodes represent the depot which is split for modeling convenience. The `Source` and `Sink` cannot have a demand, if 
one is given it is ignored with a warning.

Please read sections :ref:`vrp`, :ref:`options` and :ref:`examples` for details and examples on each of the above arguments.

