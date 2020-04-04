[![CircleCI](https://circleci.com/gh/Kuifje02/vrpy.svg?style=svg)](https://circleci.com/gh/Kuifje02/vrpy)
[![codecov](https://codecov.io/gh/Kuifje02/vrpy/branch/master/graph/badge.svg)](https://codecov.io/gh/Kuifje02/vrpy)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6f27b9ccd1c2446aa1dba15e701aa9b0)](https://app.codacy.com/manual/Kuifje02/vrpy?utm_source=github.com&utm_medium=referral&utm_content=Kuifje02/vrpy&utm_campaign=Badge_Grade_Dashboard)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Documentation Status](https://readthedocs.org/projects/vrpy/badge/?version=latest)](https://vrpy.readthedocs.io/en/latest/?badge=latest)


# VRPy
A python framework for solving the VRP and its variants with column generation.

## Requirements

[networkx](https://pypi.org/project/networkx/)

[cspy](https://pypi.org/project/cspy/)

[pulp](https://pypi.org/project/PuLP/)

<!--[ortools](https://developers.google.com/optimization/install/python)-->

## Documentation (work in progress)

[toy example](https://fr.overleaf.com/read/zmqqdbgtmmnv
)

## Usage (work in progress)

```python
from networkx import DiGraph
from vrpy import main

# Define the graph, must contain "Source" and "Sink" nodes
G = DiGraph()
G.add_edge("Source",1,cost=1,time=2)
G.add_edge("Source",2,cost=2,time=1)
G.add_edge(1,"Sink",cost=0,time=2)
G.add_edge(2,"Sink",cost=2,time=3)
G.add_edge(1,2,cost=1,time=1)

# Define a list of initial_routes
route_1 = DiGraph(cost=1)
route_1.add_path(["Source",1,"Sink"])
route_2 = DiGraph(cost=4)
route_2.add_path(["Source",2,"Sink"])
initial_routes=[route_1,route_2]

# Solve the VRP
# Optional values define constraints
main.main(G, initial_routes, cspy=True, num_stops=4)
```

## Running the tests

```sh
cd tests
pytest
```