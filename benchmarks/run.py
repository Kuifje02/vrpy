#!/usr/bin/env python
import os
from time import time
import argparse
from itertools import product
from logging import getLogger
from multiprocessing import Pool, cpu_count

from networkx import relabel_nodes, DiGraph

from benchmarks.augerat_dataset import AugeratDataSet
from benchmarks.solomon_dataset import SolomonDataSet
from benchmarks.utils.csv_table import CsvTable

from vrpy import VehicleRoutingProblem

logger = getLogger("run")

parser = argparse.ArgumentParser(description='Run benchmarks.')

parser.add_argument('--input_folder',
                    '-dir',
                    type=str,
                    default="benchmarks/data/",
                    dest="INPUT_FOLDER",
                    help='Top folder where the instances are located' +
                    ' Default: benchmarks/data/')
parser.add_argument('--instance_types',
                    '-i',
                    nargs='+',
                    dest="INSTANCE_TYPES",
                    default=["cvrp"],
                    help='Type of instance to run: crvp, cvrptw.' +
                    ' Note same name as folder in data. Default: cvrp')
parser.add_argument('--time_limit',
                    type=int,
                    default=10,
                    dest="TIME_LIMIT",
                    help='Time limit for each instance in seconds.' +
                    ' Default: 10')
parser.add_argument('--series',
                    '-s',
                    action='store_true',
                    dest="SERIES",
                    help='To run the benchmarks in series or in parallel.' +
                    ' Default: parallel')
parser.add_argument('--cpu-count',
                    '-cpu',
                    type=int,
                    default=0,
                    dest="CPU_COUNT",
                    help='Number of cpus to use. Default: all avaiable.')
parser.add_argument('--exploration',
                    '-e',
                    action='store_false',
                    dest="PERFORMANCE",
                    help='To run the benchmarks in performance mode (default)' +
                    ' or in exploration mode. Exploration mode runs' +
                    ' different solver parameters')

args = parser.parse_args()

# Set vars from arguments
INPUT_FOLDER = args.INPUT_FOLDER
INSTANCE_TYPES = args.INSTANCE_TYPES
TIME_LIMIT = args.TIME_LIMIT
SERIES = args.SERIES
CPU_COUNT = cpu_count() if not args.CPU_COUNT else args.CPU_COUNT
PERFORMANCE = args.PERFORMANCE
# Perfomance set up
PERFORMANCE_SOLVER_PARAMS = {
    'cvrp': {
        'dive': False,
        'greedy': True,
        'cspy': False,
        'pricing_strategy': 'BestEdges1'
    },
    'cvrptw': {
        'dive': False,
        'greedy': True,
        'cspy': True,
        'pricing_strategy': 'BestEdges1'
    }
}


def run_series():
    """
    Iterates through all problem instances and creates csv table
    in a new folder `benchmarks/results/` in series
    """

    for instance_type in INSTANCE_TYPES:
        path_to_instance_type = os.path.join(INPUT_FOLDER, instance_type)
        for root, _, files in os.walk(path_to_instance_type):
            for f in files:
                path_to_instance = os.path.join(root, f)
                if PERFORMANCE:
                    _run_single_problem(
                        path_to_instance,
                        **PERFORMANCE_SOLVER_PARAMS[instance_type])
                else:
                    for dive in [True, False]:
                        for cspy in [True, False]:
                            for pricing_strategy in [
                                    "BestPaths", "BestEdges1", "BestEdges2",
                                    "Exact"
                            ]:
                                for greedy in [True, False]:
                                    _run_single_problem(path_to_instance, dive,
                                                        greedy, cspy,
                                                        pricing_strategy)


def run_parallel():

    all_files = list([
        os.path.join(root, f) for instance_type in INSTANCE_TYPES
        for root, _, files in os.walk(os.path.join(INPUT_FOLDER, instance_type))
        for f in files
    ])

    if PERFORMANCE:
        # Iterate through all files
        iterate_over = all_files  # Exploration mode
    else:
        # Iterate the cartesian product of all files and solver parameters
        iterate_over = list(
            product(
                all_files,
                [False],  # dive
                [True, False],  # greedy
                [False, True],  # cspy
                ["BestPaths", "BestEdges1", "BestEdges2", "Exact"]))

    pool = Pool(processes=CPU_COUNT)
    with pool:
        res = pool.map_async(_parallel_wrapper, iterate_over)
        res.get()
    pool.close()


def _parallel_wrapper(input_tuple):
    if PERFORMANCE:
        _, instance_type, _ = _split_path_to_instance(input_tuple)
        _run_single_problem(input_tuple,
                            **PERFORMANCE_SOLVER_PARAMS[instance_type])
    else:
        _run_single_problem(*input_tuple)


def _run_single_problem(path_to_instance,
                        dive=None,
                        greedy=None,
                        cspy=None,
                        pricing_strategy=None):
    instance_folder, instance_type, instance_name = _split_path_to_instance(
        path_to_instance)
    logger.info("Solving instance %s", instance_name)
    # Load data
    if instance_type == "cvrp":
        data = AugeratDataSet(path=os.path.normpath(instance_folder),
                              instance_name=instance_name)
    elif instance_type == "cvrptw":
        data = SolomonDataSet(path=os.path.normpath(instance_folder),
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


def _split_path_to_instance(path_to_instance):
    """From a given full path to an instance, split into
    root folder, parent folder, file name
    e.g. benchmarks/cvrp, cvrp, P-50-k7.vrp
    """
    instance_folder, instance_name = os.path.split(path_to_instance)
    instance_type = os.path.basename(instance_folder)
    return instance_folder, instance_type, instance_name


def main():
    """ Run parallel or series"""
    if SERIES:
        run_series()
    else:
        run_parallel()


if __name__ == "__main__":
    main()
