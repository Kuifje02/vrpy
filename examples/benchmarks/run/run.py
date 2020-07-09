#!/usr/bin/env python

from networkx import relabel_nodes, DiGraph
import numpy as np
from pandas import read_csv
import sys
import os
import time

from itertools import product
from multiprocessing import Pool, cpu_count

from examples.benchmarks.run.csv_table_vrpy import CsvTableVRPy
from examples.benchmarks.cvrp_augerat import DataSet
from vrpy.main import VehicleRoutingProblem


def _func(input_tuple):
    """
    Creates the VRPy instance from from the folder specified by path_from and writes data in a csv_file specified by path_to
    Args:
        instance_tuple contains:
            instance_name: name of instance
            dive, greedy, cspy, pricing_strategy: parameters for the VRPy problem
            path_from: folder path with instance data
            path_to: folder path to add the data
    """
    instance_name, dive, greedy, cspy, pricing_strategy, path_from, path_to = input_tuple

    #bør jeg lage en ny instance hver gang?
    #add numstops?

    #kan jeg gjøre det som står i data set uten å bruke data set?
    data = DataSet(path=path_from, instance_name=instance_name)

    table = CsvTableVRPy(path=path_from, instance_name=instance_name)
    table.write_to_file(path_to=path_to)

    #how do i set up vehicle routing problem?
    prob = VehicleRoutingProblem(data.G, load_capacity=data.max_load)

    prob.solve(dive=dive,
               greedy=greedy,
               cspy=cspy,
               pricing_strategy=pricing_strategy,
               time_limit=5,
               compute_runtime=True)

    table.get_data_from_VRPy_instance(dive=dive,
                                      cspy=cspy,
                                      pricing_strategy=pricing_strategy,
                                      greedy=greedy,
                                      comp_time=prob.comp_time,
                                      best_value=prob.best_value,
                                      lower_bound=prob._lower_bound[-1])
    table.write_to_file(path_to=path_to)
    return


def run_parallel(path_from=None, path_to=None):
    """
    Parallellised iteration through a folder of instances.
    Args:
        path_from: specifies the path of the folder to iterate through
        path_to: specifies the path where to add the data. 
    """

    product_all = list(
        product(
            [os.fsdecode(file) for file in os.listdir(path_from)
             ],  # assume all are .vrp instances
            [True, False],  # dive
            [True, False],  # greedy
            [True, False],  # cspy
            ["BestPaths", "BestEdges1", "BestEdges2", "Exact"],
            [path_from],
            [path_to]))

    pool = Pool(processes=1)  # picklin
    with pool:
        res = pool.map_async(_func, product_all)
        res.get()
    pool.close()


def iterate_through_instances_single_thread(data_from=None, time_limit=100):
    """ 
    Iterates through all problem instances and prints performance profile in results folder without parallellisation 
    """
    if not data_from == None:
        path = data_from
    else:
        path = "examples/benchmarks/data/cvrp/"

    for file in os.listdir(path):
        filename = os.fsdecode(file)
        if filename.endswith(".vrp"):
            for dive in [True, False]:
                for subproblem_type in ["lp", "cspy"]:
                    if subproblem_type == "cspy":
                        cspy = True
                    else:
                        cspy = False
                    for pricing_strategy in [
                            "BestPaths", "BestEdges1", "BestEdges2", "Exact"
                    ]:
                        for greedy in [True, False]:
                            data = DataSet(path=path, instance_name=filename)
                            data.solve(dive=dive,
                                       cspy=cspy,
                                       greedy=greedy,
                                       time_limit=time_limit,
                                       pricing_strategy=pricing_strategy)

        else:
            continue


def iterate_through_instances_multi_thread(path_from=None,
                                           path_to=None,
                                           time_limit=100):
    """
    Iterates through all problem instances and prints performance profile in results folder using parallellisation
    """
    if not path_from == None:
        path_from = path_from
    else:
        #Run from vrpy
        path_from = "examples/benchmarks/data/cvrp/"
    run_parallel(path_from=path_from, path_to=path_to)


if __name__ == "__main__":
    #Specify absolute paths
    path_from = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/data/cvrp/'
    path_to = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/run/'
    iterate_through_instances_multi_thread(path_from=path_from,
                                           path_to=path_to)
