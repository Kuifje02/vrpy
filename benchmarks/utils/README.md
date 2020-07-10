
#
csv table and subclasses are a python classes which take input in the form of problem instance files and writes profiling results in a csv_files

| instance | pricing heuristic | subproblem type | Dived | CPU time (s) | % Integrality Gap | % Optimality Gap | optimal solution |
|----|---|---|---|---|---|----|---|
|c101 | Exact | cspy | True | 0.00001 | 0 | 0 | 0 |

The subclass CsvTableVRPy computes the relvant values from a problem instance.

## Contains

### The base class CsvTableBase:
- Initialised with path and instance name creates and writes to folder

### The derived class CsvTableVRPy:
### The run file
- The run file is a script which iterates through a folder of instances and calls CsvTables to write to a file in the results folder



## Usage
### With developer mode
- If you don't have vrpy in developer mode, run ```bash python3 -m pip install -e```
- Add instances ending with .vrp in the folder ```/vrpy/examples/benchmarks/data/cvrp```
- In run.py, set path_from absolute path of ```/vrpy/examples/benchmarks/data/cvrp```, path_to to absolute path ending in
```/vrpy/examples/benchmarks/run/results```.
- Do ```bash python3 examples/benchmarks/run/run.py```

### Run as a module
- In run.py, set path_from absolute path of ```/vrpy/examples/benchmarks/data/cvrp```, path_to to absolute path ending in
```/vrpy/examples/benchmarks/run/results```.
- Do ```bash python3 -m examples.benchmarks.run.run```

Files are added to the folder ending in ```benchmarks/run/results```
