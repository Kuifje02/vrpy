[![CircleCI](https://circleci.com/gh/Kuifje02/vrpy.svg?style=svg)](https://circleci.com/gh/Kuifje02/vrpy)
[![codecov](https://codecov.io/gh/Kuifje02/vrpy/branch/master/graph/badge.svg)](https://codecov.io/gh/Kuifje02/vrpy)
# VRPy
A python framework for solving the VRP and its variants with column generation.

## Requirements

[networkx](https://pypi.org/project/networkx/)

[cspy](https://pypi.org/project/cspy/)

[pulp](https://pypi.org/project/PuLP/)

[ortools](https://developers.google.com/optimization/install/python)

## Usage

Right now, only a [toy example](https://fr.overleaf.com/read/zmqqdbgtmmnv
) is considered. 

Go to ~/vrpy/main.py and modify the following options to activate the different constraints. 

```python
# Parameters
CSPY = True  # use cspy for subproblem, otherwise use LP
MAX_STOP = True  # max 3 stops per vehicle
MAX_LOAD = False  # max 10 units per vehicle
MAX_TIME = False  # max 60 minutes per vehicle
```

Then run the main script :

```sh
cd ~/vrpy
python main.py
```



## Running the tests

```sh
cd tests
pytest
```