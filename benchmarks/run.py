#!/usr/bin/env python

import os
from time import time
import argparse
from itertools import product
from multiprocessing import Pool, cpu_count

from networkx import relabel_nodes, DiGraph

from benchmarks.augerat_dataset import AugeratDataSet
from benchmarks.solomon_dataset import SolomonDataSet
from benchmarks.utils.csv_table import CsvTable

from vrpy import VehicleRoutingProblem

parser = argparse.ArgumentParser(description='Run benchmarks.')
parser.add_argument('--instance_types',
                    nargs='+',
                    dest="INSTANCE_TYPES",
                    help='Type of instance to run: crvp, cvrptw')
parser.add_argument('--time_limit',
                    type=int,
                    default=100,
                    dest="TIME_LIMIT",
                    help='Time limit for each instance in seconds')
args = parser.parse_args()
# Set global vars
INSTANCE_TYPES = args.INSTANCE_TYPES
TIME_LIMIT = args.TIME_LIMIT


def run_series(input_folder=None, time_limit=100):
    """
    Iterates through all problem instances and creates csv table
    in a new folder `benchmarks/results/` in series
    """
    if input_folder is None:
        input_folder = "benchmarks/data/"

    for instance_type in INSTANCE_TYPES:
        path_to_instance_type = input_folder + instance_type + "/"
        for file in os.listdir(path_to_instance_type):
            filename = os.fsdecode(file)
            if filename.endswith(".vrp"):
                for dive in [True, False]:
                    for cspy in [True, False]:
                        for pricing_strategy in [
                                "BestPaths", "BestEdges1", "BestEdges2", "Exact"
                        ]:
                            for greedy in [True, False]:
                                pass
                                # TODO fix to call _run_single_problem
            else:
                continue


def run_parallel(input_folder=None, output_folder=None):
    if input_folder is None:
        input_folder = "benchmarks/data/"

    product_all = list(
        product(
            [
                os.path.join(root, f) for instance_type in INSTANCE_TYPES
                for root, _, files in os.walk(input_folder + instance_type +
                                              "/") for f in files
            ],
            [True, False],  # dive
            [True, False],  # greedy
            [True, False],  # cspy
            ["BestPaths", "BestEdges1", "BestEdges2", "Exact"]))
    pool = Pool(processes=1)
    with pool:
        res = pool.map_async(_parallel_wrapper, product_all)
        res.get()
    pool.close()


def _parallel_wrapper(input_tuple):
    _run_single_problem(*input_tuple)
    return


def _run_single_problem(path_to_instance, dive, cspy, greedy, pricing_strategy):
    instance_folder, instance_name = os.path.split(path_to_instance)
    instance_type = os.path.basename(instance_folder)
    # Load data
    if instance_type == "cvrp":
        data = AugeratDataSet(path=os.path.normpath(instance_folder),
                              instance_name=instance_name)
    elif instance_type == "cvrptw":
        data = SolomonDataSet(path=instance_folder + os.sep,
                              instance_name=instance_name)
    # Solve problem
    prob = VehicleRoutingProblem(data.G,
                                 load_capacity=data.max_load,
                                 time_windows=bool(instance_type == "cvrptw"))
    start = time()
    prob.solve(dive=dive,
               cspy=cspy,
               greedy=greedy,
               time_limit=TIME_LIMIT,
               pricing_strategy=pricing_strategy)
    # Output results
    table = CsvTable(instance_name=instance_name,
                     comp_time=time() - start,
                     best_known_solution=data.best_known_solution,
                     instance_type=instance_type)
    table.from_vrpy_instance(prob)


def main():
    # run_series()
    run_parallel()


if __name__ == "__main__":
    main()
