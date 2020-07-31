.. _benchmarks:

Performance profiles
====================

Performance profiles are a practical way to have a global overview of a set of algorithms' performances. 
On the :math:`x` axis, we have the relative gap (%), and on the :math:`y` axis, the percentage of data sets solved within the gap. 
So for example, at the intersection with the :math:`y` axis is the percentage of data sets solved optimally, 
and at the intersection with  :math:`y=100\%`  is the relative gap within which all data sets are solved.

At a glance, the more the curve is in the upper left corner, the better the algorithm.

We compare the performances of `vrpy` and `OR-Tools` (default options):

-   on Augerat_'s instances (CVRP),
-   on Solomon_'s instances (CVRPTW)

Results are found here_ [link to repo] and can be replicated.

CVRP
----

.. figure:: images/cvrp_performance_profile.png
   :align: center
   
We can see that with a maximum running time of :math:`10` seconds, `OR-Tools` solves :math:`15\%` of the instances optimally, 
while `vrpy` only solves :math:`5\%` of them. Both solve approximately :math:`43\%` of instances with a maximum relative gap of :math:`5\%`.
And both solve all instances within a maximum gap of :math:`25\%`.

CVRPTW
------

Coming soon.

.. _Augerat: https://neo.lcc.uma.es/vrp/vrp-instances/capacitated-vrp-instances/
.. _Solomon: https://neo.lcc.uma.es/vrp/vrp-instances/capacitated-vrp-with-time-windows-instances/
.. _here: 