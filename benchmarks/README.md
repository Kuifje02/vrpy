# Results

Some summary tables and plots coming soon.

# Replicating results

## Set up

First download the instances you wish to run ([Augerat]() or [Solomon]()) and place them in the
appropriate folders:
 -  Augerat -> `benchmarks/data/cvrp`,
 -  Solomon -> `benchmarks/data/cvrptw`.

For Augerat, ensure that no `.sol` files are left in the folder

## Running

To run the results with the default configuration, from the root folder of the project (`vrpy/`), do

```bash
python3 -m benchmarks.run
```

As it goes, the csv files are created in a new `benchmarks/run/results`.

To see the different options do

```bash
python3 -m benchmarks.run -h
```

These include:
 - Parallel/series runner
 - CPU number specificiation
 - Exploration or performance mode (default configuration)

## OR-TOOLS

To run tests with ortools, [this code](https://github.com/Kuifje02/ortools) can be used.
