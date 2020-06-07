---
title: 'VRPy: A Python package for solving a collection of vehicle routing problems'
tags:
  - Python
  - Vehicle Routing Problems
  - Networks
  - Column generation
authors:
  - name: Romain Montagné
    orcid: 0000-0003-3139-4519
    affiliation: "2"
  - name: David Torres Sanchez
    orcid: 0000-0002-2894-9432
    affiliation: "1"
affiliations:
 - name: SINTEF Digital, Mathematics and Cybernetics
   index: 1
 - name: EURODECISION
   index: 2
date: June 2020
bibliography: paper.bib
---

# Introduction

The Vehicle Routing Problem (VRP) is amongst the most well known combinatorial optimization problems. The most classical version of the VRP, the Capacitated VRP (CVRP), can be described as follows. A fleet of vehicles with uniform capacity must serve customers with known demand for a single commodity.
The vehicles start and end their routes at a common depot and each customer must be served by exactly one vehicle.
The objective is to assign a sequence of customers to each truck of the fleet (a route), minimizing the total distance traveled, such that all customers are served and the total demand served by each truck does not exceed its capacity. Note that the VRP generalises the well-known traveling salesman problem (TSP) and is therefore computationally intractable.

Mathematicians have started tackling VRPs since 1959 [@dantzig1959truck]. Ever since, algorithms and computational power have not stopped improving. State of the art techniques include column generation approaches  [@costa2019exact] on which ``vrpy`` relies; more details are given in the following section.

``vrpy`` is of interest to the operational research community and others (e.g., logisticians, supply chain analysts) who wish to solve vehicle routing problems, and therefore has many obvious applications in industry.


# Features

``vrpy`` is a Python package that allows one to solve variants of the VRP including:

-   the Capacitated VRP (CVRP),
-   the CVRP with resource constraints,
-   the CVRP with time windows (CVRPTW),
-   the CVRP with simultaneous distribution and collection (CVRPSDC),
-   the CVRP with heterogeneous fleet (HFCVRP).


For each of these variants, it is possible to i/ set initial routes for the search (if one already has a solution at hand and wishes to improve it) ii/ lock routes (if part of the solution is imposed and must not be optimized) iii/ drop nodes (ignore a customer at the cost of a penalty).

# Mathematical background

``vrpy`` solves vehicle routing problems with a column generation approach. The term *column generation* refers to the fact that iteratively, routes (or columns) are generated with a pricing problem, and fed to a master problem which selects the best routes among a pool such that each vertex is serviced exactly once. This procedure is illustrated in the Figure 1 below:

<!---
![Column Generation.\label{fig:colgen}](colgen.png)
*Column Generation*
--->

| ![Column Generation](colgen.png) |
| :------------------------------: |
|  *Figure 1: Column Generation*   |

The master problem is a set partitioning linear formulation, while the sub problem is a shortest elementary path problem with *resource constraints*, hence the interest of using the ``cspy`` library (@cspy) which is designed to solve such problems.

# Examples

<!---
The package has been used in the following examples:

- [`vrpy`](https://github.com/Kuifje02/vrpy) : vehicle routing framework which solves different variants of the vehicle routing problem (including capacity constraints and time-windows) using column generation. The framework has been tested on standard vehicle routing instances.
- [`cgar`](https://github.com/torressa/cspy/tree/master/examples/cgar) : Complex example using column generation applied to the aircraft recovery problem.
- [`jpath`](https://github.com/torressa/cspy/tree/master/examples/jpath) : Simple example showing the necessary graph adaptations and the use of custom resource extension functions.
-->

# Acknowledgements


# References