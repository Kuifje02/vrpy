from time import time
import argparse
from itertools import product
from logging import getLogger
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import List, Dict, Union

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
                    '-t',
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
INPUT_FOLDER: Path = Path(args.INPUT_FOLDER)
INSTANCE_TYPES: List[str] = args.INSTANCE_TYPES
TIME_LIMIT: int = args.TIME_LIMIT
SERIES: bool = args.SERIES
CPU_COUNT: int = cpu_count() if not args.CPU_COUNT else args.CPU_COUNT
PERFORMANCE: bool = args.PERFORMANCE
# Perfomance set up
PERFORMANCE_SOLVER_PARAMS: Dict[str, Dict[str, Union[bool, str]]] = {
    'cvrp': {
        'dive': False,
        'greedy': True,
        'cspy': False,
        'pricing_strategy': 'Hyper',
        'time_limit': TIME_LIMIT,
        'max_iter': 1,
        'run_exact': 30
    },
    'cvrptw': {
        'dive': False,
        'greedy': True,
        'cspy': False,
        'pricing_strategy': 'BestEdges1',
        'max_iter': 1,
        'time_limit': TIME_LIMIT,
        'run_exact': 30
    }
}


def run_series():
    """Iterates through all problem instances and creates csv table
    in a new folder `benchmarks/results/` in series
    """
    for instance_type in INSTANCE_TYPES:
        path_to_instance_type = INPUT_FOLDER / instance_type
        for path_to_instance in path_to_instance_type.glob("*"):
            if PERFORMANCE:
                _run_single_problem(path_to_instance,
                                    **PERFORMANCE_SOLVER_PARAMS[instance_type])
            else:
                for dive in [True, False]:
                    for cspy in [True, False]:
                        for pricing_strategy in [
                                "BestPaths", "BestEdges1", "BestEdges2",
                                "Exact", "Hyper"
                        ]:
                            for greedy in [True, False]:
                                _run_single_problem(
                                    path_to_instance,
                                    dive=dive,
                                    greedy=greedy,
                                    cspy=cspy,
                                    pricing_strategy=pricing_strategy)


def run_parallel():
    """Iterates through the instances using in parallel using CPU_COUNT.
    """
    all_files = [
        path_to_instance for instance_type in INSTANCE_TYPES
        for path_to_instance in Path(INPUT_FOLDER / instance_type).glob("*")
    ]

    if PERFORMANCE:
        # Iterate through all files
        iterate_over = all_files  # Exploration mode
    else:
        # Iterate the cartesian product of all files and solver parameters
        iterate_over = list(
            product(
                all_files,
                [False],  # dive
                [True],  # greedy
                [True, False],  # cspy
                ["Hyper"]))
    pool = Pool(processes=CPU_COUNT)
    with pool:
        res = pool.map_async(_parallel_wrapper, iterate_over)
        res.get()
    pool.close()


def _parallel_wrapper(input_tuple):
    if PERFORMANCE:
        path_to_instance = input_tuple
        instance_type = path_to_instance.parent.stem
        _run_single_problem(path_to_instance,
                            **PERFORMANCE_SOLVER_PARAMS[instance_type])
    else:
        kwargs = dict(
            zip([
                "path_to_instance", "dive", "greedy", "cspy", "pricing_strategy"
            ], input_tuple))
        _run_single_problem(**kwargs)


def _run_single_problem(path_to_instance: Path, **kwargs):
    'Run single problem with solver arguments as in kwargs'
    instance_folder = path_to_instance.parent
    instance_type = path_to_instance.parent.stem
    instance_name = path_to_instance.name
    logger.info("Solving instance %s", instance_name)
    # Load data
    if instance_type == "cvrp":
        data = AugeratDataSet(path=instance_folder, instance_name=instance_name)
    elif instance_type == "cvrptw":
        data = SolomonDataSet(path=instance_folder, instance_name=instance_name)
    # Solve problem
    prob = VehicleRoutingProblem(data.G,
                                 load_capacity=data.max_load,
                                 time_windows=bool(instance_type == "cvrptw"))
    prob.solve(**kwargs)
    # Output results
    table = CsvTable(instance_name=instance_name,
                     comp_time=prob.comp_time,
                     best_known_solution=data.best_known_solution,
                     instance_type=instance_type)
    table.from_vrpy_instance(prob)


def main():
    """ Run parallel or series"""
    if SERIES:
        run_series()
    else:
        run_parallel()


if __name__ == "__main__":
    main()
