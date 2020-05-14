[![CircleCI](https://circleci.com/gh/Kuifje02/vrpy.svg?style=svg)](https://circleci.com/gh/Kuifje02/vrpy)
[![codecov](https://codecov.io/gh/Kuifje02/vrpy/branch/master/graph/badge.svg)](https://codecov.io/gh/Kuifje02/vrpy)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6f27b9ccd1c2446aa1dba15e701aa9b0)](https://app.codacy.com/manual/Kuifje02/vrpy?utm_source=github.com&utm_medium=referral&utm_content=Kuifje02/vrpy&utm_campaign=Badge_Grade_Dashboard)
[![Python 3.8](https://img.shields.io/badge/python-3.6|3.7|3.8-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Documentation Status](https://readthedocs.org/projects/vrpy/badge/?version=latest)](https://vrpy.readthedocs.io/en/latest/?badge=master)

# VRPy

VRPy is a python framework for solving Vehicle Routing Problems (VRP) including:

- the Capacitated VRP (CVRP),
- the CVRP with resource constraints,
- the CVRP with time windows (CVRPTW),
- the CVRP with simultaneous distribution and collection.

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
G.nodes[1]["demand"] = 5
G.nodes[2]["demand"] = 4

# Define the Vehicle Routing Problem
prob = VehicleRoutingProblem(G, load_capacity=10, duration=5)

# Solve and display solution value
prob.solve()
prob.best_value
3
prob.best_routes
[["Source",2,1,"Sink"]]
```

## Install

Coming soon.

## Requirements

[cspy](https://pypi.org/project/cspy/)

[NetworkX](https://pypi.org/project/networkx/)

[pandas](https://pypi.org/project/pandas/)

[PuLP](https://pypi.org/project/PuLP/)

<!--[ortools](https://developers.google.com/optimization/install/python)-->

## Documentation

Documentation is found [here](https://vrpy.readthedocs.io/en/latest/).

## Running the tests

### Unit Tests

```sh
cd tests
pytest unittests/
```

### Benchmarks

```sh
cd tests
pytest benchmarks/
```

## Bugs

Please report any bugs that you find [here](https://github.com/Kuifje02/vrpy/issues). Or, even better, fork the repository on [GitHub](https://github.com/Kuifje02/vrpy) and create a pull request. Any contributions are welcome.
