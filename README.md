[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6f27b9ccd1c2446aa1dba15e701aa9b0)](https://app.codacy.com/manual/Kuifje02/vrpy?utm_source=github.com&utm_medium=referral&utm_content=Kuifje02/vrpy&utm_campaign=Badge_Grade_Dashboard)
[![CircleCI](https://circleci.com/gh/Kuifje02/vrpy.svg?style=svg)](https://circleci.com/gh/Kuifje02/vrpy)
[![codecov](https://codecov.io/gh/Kuifje02/vrpy/branch/master/graph/badge.svg)](https://codecov.io/gh/Kuifje02/vrpy)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9b8a07701e54401aa71a1db7dba4d462)](https://www.codacy.com/manual/Kuifje02/vrpy?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Kuifje02/vrpy&amp;utm_campaign=Badge_Grade)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-360/)

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
TIME_WINDOWS = True  # time window constraints on each node
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