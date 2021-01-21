---
title: 'VRPy: A Python package for solving a range of vehicle routing problems with a column generation approach'
tags:
  - Python
  - Vehicle Routing Problems
  - Networks
  - Column generation
authors:
  - name: Romain Montagné
    orcid: 0000-0003-3139-4519
    affiliation: "1"
  - name: David Torres Sanchez
    orcid: 0000-0002-2894-9432
    affiliation: "2"
  - name: Halvard Olsen Storbugt
    orcid: 0000-0003-1142-0185
    affiliation: "2"
affiliations:
 - name: EURODECISION
   index: 1
 - name: SINTEF Digital, Mathematics and Cybernetics
   index: 2
date: June 2020
bibliography: paper.bib
---

# Introduction

The Vehicle Routing Problem (VRP) is amongst the most well known combinatorial optimization problems. The most classical version of the VRP, the Capacitated VRP (CVRP) [@laporte2007you], can be described as follows. A fleet of vehicles with uniform capacity must serve customers with known demand for a single commodity.
The vehicles start and end their routes at a common depot and each customer must be served by exactly one vehicle.
The objective is to assign a sequence of customers to each vehicle of the fleet (a route), minimizing the total distance traveled, such that all customers are served and the total demand served by each vehicle does not exceed its capacity. Note that the VRP generalises the well-known traveling salesman problem (TSP) and is therefore computationally intractable.

Mathematicians have started tackling VRPs since 1959 [@dantzig1959truck]. Ever since, algorithms and computational power have not stopped improving. State of the art techniques include column generation approaches  [@costa2019exact; @bramel1997solving] on which ``vrpy`` relies; more details are given hereafter.

``vrpy`` is of interest to the operational research community and others (e.g., logisticians, supply chain analysts) who wish to solve vehicle routing problems, and therefore has many obvious applications in industry.

# Features

``vrpy`` is a Python package that offers an easy-to-use, unified API for many variants of vehicle routing problems including:

-   the Capacitated VRP (CVRP) [@laporte2007you;@baldacci2010exact],
-   the CVRP with resource constraints [@laporte1985optimal],
-   the CVRP with time windows  [@cordeau2000vrp],
-   the CVRP with simultaneous distribution and collection [@dell2006branch],
-   the CVRP with pickups and deliveries [@desrosiers1988shortest],
-   the CVRP with heterogeneous fleet [@choi2007column].

For each of these variants, it is possible to i/ set initial routes for the search (if one already has a solution at hand and wishes to improve it) ii/ lock routes (if part of the solution is imposed and must not be optimized) iii/ drop nodes (ignore a customer at the cost of a penalty).

``vrpy`` is built upon the well known *NetworkX* library [@hagberg2008exploring] and thus benefits from a user friendly API, as shown in the following quick start example:

```python
from networkx import DiGraph
from vrpy import VehicleRoutingProblem

# Define the network
G = DiGraph()
G.add_edge("Source",1,cost=1,time=2)
G.add_edge("Source",2,cost=2,time=1)
G.add_edge(1,"Sink",cost=0,time=2)
G.add_edge(2,"Sink",cost=2,time=3)
G.add_edge(1,2,cost=1,time=1)
G.add_edge(2,1,cost=1,time=1)

# Define the customers demands
G.nodes[1]["demand"] = 5
G.nodes[2]["demand"] = 4

# Define the Vehicle Routing Problem
prob = VehicleRoutingProblem(G, load_capacity=10, duration=5)

# Solve and display solution value
prob.solve()
print(prob.best_value)
3
print(prob.best_routes)
{1: ["Source",2,1,"Sink"]}
```

# State of the field

Although the VRP is a classical optimization problem, to our knowledge there is only one dedicated package in the Python ecosystem that is able to solve such a range of VRP variants: the excellent ``OR-Tools`` (Google) routing library [@ortools], released for the first time in 2014. To be precise, the core algorithms are implemented in C++, but the library provides a wrapper in Python. Popular and efficient, it is a reference for ``vrpy``, both in terms of features and performance. The current version of ``vrpy`` is able to handle the same variants as OR-Tools (mentioned in the previous section).

Performance-wise, ``vrpy`` ambitions to be competitive with ``OR-Tools`` eventually, at least in terms of solution quality. For the moment, benchmarks (available in the repository) for the CVRP on the set of Augerat instances [@augerat1995approche] show promising results: in the performance profile in Figure 1 below, one can see that nearly the same number of instances are solved within 10 seconds with the same relative error with respect to the best known solution (42\% for ``vrpy``, 44\% for ``OR-Tools``).

| ![Performance profile](cvrp_performance_profile.png) |
| :--------------------------------------------------: |
|         *Figure 1: CVRP Performance profile*         |

We do not claim to outperform ``OR-Tools``, but aim to have results of the same order of magnitude as the package evolves, as there is still much room for improvement (see Section *Future Work* below). On the other hand, we are confident that the user friendly and intuitive API will help students, researchers and more generally the operational research community solve instances of vehicle routing problems of small to medium size, perhaps more easily than with the existing software.

``py-ga-VRPTW`` is another library that is available but as mentioned by its authors, it is more of an experimental project and its performances are rather poor. In particular, we were not able to find feasible solutions for Solomon's instances [@solomon1987algorithms] and therefore cannot compare the two libraries. Also note that ``py-ga-VRPTW`` is designed to solve the VRPTW only, that is, the VRP with time windows.


# Mathematical background

``vrpy`` solves vehicle routing problems with a column generation approach. The term *column generation* refers to the fact that iteratively, routes (or columns) are generated with a pricing problem, and fed to a master problem which selects the best routes among a pool such that each vertex is serviced exactly once. Results from the master problem are then used to search for new potential routes likely to improve the solution's cost, and so forth. This procedure is illustrated in Figure 2 below:

| ![Column Generation](colgen.png) |
| :------------------------------: |
|  *Figure 2: Column Generation*   |

The master problem is a set partitioning linear formulation and is solved with the open source solver Clp from COIN-OR [@johnjforrest_2020_clp], while the subproblem is a shortest elementary path problem with *resource constraints*. It is solved with the help of the  ``cspy`` library [@cspy] which is specifically designed for such problems.

This column generation procedure is very generic, as for each of the featuring VRP variants, the master problem is identical and partitions the customers into subsets (routes). It is the subproblem (or pricing problem) that differs from one variant to another. More specifically, each variant has its unique set of *resources* which must remain in a given interval. For example, for the CVRP, a resource representing the vehicle's load is carried along the path and must not exceed the vehicle capacity; for the CVRP with time windows, two extra resources must be considered: the first one for time, and the second one for time window feasibility. The reader may refer to [@costa2019exact] for more details on each of these variants and how they are delt with within the framework of column generation.

Note that ``vrpy`` does not necessarily return an optimal solution. Indeed, once the pricing problems fails to find
a route with negative marginal cost, the master problem is solved as a MIP. This *price-and-branch* strategy does not guarantee optimality. Note however that it
can be shown [@bramel1997solving] that asymptotically, the relative error goes to zero as the number of customers increases. To guarantee that an optimal solution is returned, the column generation procedure should be embedded in a branch-and-bound scheme (*branch-and-price*), which is beyond the scope of the current release, but part of the future work considered.

# Advanced Features

For more advanced users, there are different pricing strategies (approaches for solving subproblems), namely sparsification strategies [@dell2006branch;@santini2018branch], as well as pre-pricing heuristics available that can lead to faster solutions. The heuristics implemented include a greedy randomized heuristic
(for the CVRP and the CVRP with resource constraints) [@santini2018branch]. Also, a diving heuristic [@sadykov2019primal] can be called to explore part of the branch-and-price tree, instead of solving the restricted master problem as a MIP.

Additionally, we have an experimental feature that uses Hyper-Heuristics for the dynamic selection of
pricing strategies.
The approach ranks the best pricing strategies as the algorithm is running and chooses
according to selection functions based on [@sabar2015math;@ferreira2017multi]. The selection criteria has been modified to include a combination of runtime, objective improvement, and currently active columns in the restricted master problem.
Adaptive parameter settings found in [@drake2012improved] is used to balance exploration and exploitation
under stagnation. The main advantage is that selection is done as the program runs, and is therefore more
flexible compared to a predefined pricing strategy.

# Future Work

There are many ways ``vrpy`` could be improved. To boost the run times, specific heuristics for each variant could be implemented, e.g., Solomon's insertion algorithm [@solomon1987algorithms] for the VRPTW. Second, the pricing problem is solved with ``cspy``, which is quite recent (2019) and is still being fine tuned.  Also, currently, stabilization issues are delt with a basic interior point based strategy which could be enhanced [@pessoa2018automation]. Last but not least, there are many cutting strategies in the literature [@costa2019exact] that have not been implemented and which have proven to significantly reduce run times for such problems.

# Acknowledgements

We would like to thank reviewers Ben Stabler and Serdar Kadioglu for their helpful and constructive suggestions.

# References
