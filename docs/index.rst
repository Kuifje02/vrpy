VRPy Documentation
====================

VRPy is a python framework for solving instances of different types of Vehicle Routing Problems (VRP) including:

-   the Capacitated VRP (CVRP),
-   the CVRP with resource constraints,
-   the CVRP with time windows (CVRPTW),
-   the CVRP with simultaneous distribution and collection (CVRPSDC),
-   the CVRP with heterogeneous fleet (HFCVRP).

Check out section :ref:`vrp` to find more variants and options.

VRPy relies on the well known NetworkX_ package (graph manipulation), as well as on cspy_, a library for solving the resource constrained shortest path problem.

.. _NetworkX: Graph manipulation and creation.
.. _cspy: https://pypi.org/project/cspy/
   
Disclaimer
==========

There is no guarantee that VRPy returns the optimal solution. See section :ref:`colgen` for more details, and section :ref:`benchmarks`
for performance comparisons with OR-Tools_. 

.. _OR-Tools: https://developers.google.com/optimization/routing/vrp

Authors
=======

Romain Montagné (r.montagne@hotmail.fr)

David Torres Sanchez (d.torressanchez@lancs.ac.uk)

Contributors
============

@Halvaros

Table of contents
=================

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   getting_started
   how_to
   vrp_variants
   solving_options
   examples
   api
   mathematical_background
   benchmarks
   bibliography

* :ref:`genindex`
* :ref:`search`
