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
from vrpy.main import VRPSolver

# Define the graph, must contain "Source" and "Sink" nodes
G = DiGraph()
G.add_edge("Source",1,cost=1,time=2)
G.add_edge("Source",2,cost=2,time=1)
G.add_edge(1,"Sink",cost=0,time=2)
G.add_edge(2,"Sink",cost=2,time=3)
G.add_edge(1,2,cost=1,time=1)
G.nodes[1]["demand"] = 5
G.nodes[2]["demand"] = 4

# Solve the VRP
# Optional values define constraints
prob = VRPSolver(G, cspy=True, num_stops=4, load_capacity = 10)
prob.solve()
```

## Running the tests

```sh
cd tests
pytest
```