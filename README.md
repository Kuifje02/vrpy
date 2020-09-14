[![CircleCI](https://circleci.com/gh/Kuifje02/vrpy.svg?style=svg)](https://circleci.com/gh/Kuifje02/vrpy)
[![codecov](https://codecov.io/gh/Kuifje02/vrpy/branch/master/graph/badge.svg)](https://codecov.io/gh/Kuifje02/vrpy)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6f27b9ccd1c2446aa1dba15e701aa9b0)](https://app.codacy.com/manual/Kuifje02/vrpy?utm_source=github.com&utm_medium=referral&utm_content=Kuifje02/vrpy&utm_campaign=Badge_Grade_Dashboard)
[![Python 3.8](https://img.shields.io/badge/python-3.6|3.7|3.8-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Documentation Status](https://readthedocs.org/projects/vrpy/badge/?version=latest)](https://vrpy.readthedocs.io/en/latest/?badge=master)
[![status](https://joss.theoj.org/papers/77c3aa9b9cb3ff3d5c32d253922ad390/status.svg)](https://joss.theoj.org/papers/77c3aa9b9cb3ff3d5c32d253922ad390)

# VRPy

VRPy is a python framework for solving Vehicle Routing Problems (VRP) including:

-   the Capacitated VRP (CVRP),
-   the CVRP with resource constraints,
-   the CVRP with time windows (CVRPTW),
-   the CVRP with simultaneous distribution and collection (CVRPSDC),
-   the CVRP with heterogeneous fleet (HFCVRP).

Check out the [docs](https://vrpy.readthedocs.io/en/latest/) to find more variants and options.

## Simple example

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

## Install

```sh
pip install vrpy
```

## Requirements

[cspy](https://pypi.org/project/cspy/)

[NetworkX](https://pypi.org/project/networkx/)

[numpy](https://pypi.org/project/numpy/)

[PuLP](https://pypi.org/project/PuLP/)

## Documentation

Documentation is found [here](https://vrpy.readthedocs.io/en/latest/).

## Running the tests

### Unit Tests

```sh
python3 -m pytest tests/
```

### Benchmarks

To run some non-regression tests on some benchmarks instances (Solomon and Augerat) do

```sh
python3 -m pytest benchmarks/
```

Note that running the benchmarks requires [pandas](https://pypi.org/project/pandas/) and that it takes a while.

For more information and to run more instances, see the [benchmarks](benchmarks/README.md).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Kuifje02/vrpy/blob/dev/LICENSE) file for details.

## Bugs

Please report any bugs that you find [here](https://github.com/Kuifje02/vrpy/issues). Or, even better, fork the repository on [GitHub](https://github.com/Kuifje02/vrpy) and create a pull request. Please read the [Community Guidelines](https://github.com/Kuifje02/vrpy/blob/dev/CONTRIBUTING.md) before contributing. Any contributions are welcome.
