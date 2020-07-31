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
    Creates the VRPy instance from from the folder specified by path_instance_data and writes data in a csv_file specified by path_results_folder
    Args:
        instance_tuple contains:
            instance_name: name of instance
            dive, greedy, cspy, hyper, pricing_strategy: parameters for the VRPy problem
            path_instance_data: folder path with instance data
            path_results_folder: folder path to add the data
    """
    instance_name, dive, greedy, cspy, hyper, pricing_strategy, path_instance_data, path_results_folder = input_tuple
    #kan jeg gjøre det som står i data set uten å bruke data set?
    data = DataSet(path=path_instance_data, instance_name=instance_name)

    table = CsvTableVRPy(path=path_instance_data, instance_name=instance_name)

    #how do i set up vehicle routing problem?
    prob = VehicleRoutingProblem(data.G,
                                 load_capacity=data.max_load,
                                 use_hyper_heuristic=hyper)

    prob.solve(dive=dive,
               greedy=greedy,
               cspy=cspy,
               pricing_strategy=pricing_strategy,
               time_limit=5,
               compute_runtime=True)  #hyper here

    table.get_data_from_VRPy_instance(dive=dive,
                                      cspy=cspy,
                                      pricing_strategy=pricing_strategy,
                                      greedy=greedy,
                                      comp_time=prob.comp_time,
                                      best_value=prob.best_value,
                                      lower_bound=prob._lower_bound[-1],
                                      hyper=hyper)
    table.write_to_file(path_results_folder=path_results_folder)
    return


def run_parallel(path_instance_data=None, path_results_folder=None):
    """
    Parallellised iteration through a folder of instances.
    Args:
        path_instance_data: specifies the path of the folder to iterate through
        path_results_folder: specifies the path where to add the data. 
    """
    #Problems with the multithread

    product_all = list(
        product(
            [os.fsdecode(file) for file in os.listdir(path_instance_data)
             ],  # assume all are .vrp instances
            [False],  # dive
            [True],  # greedy
            [False],  # cspy
            [True, False],  # hyperheurs
            ["BestPaths"],  #, "BestEdges1", "BestEdges2", "Exact"],
            [path_instance_data],
            [path_results_folder]))

    pool = Pool(processes=4)  # picklin
    with pool:
        res = pool.map_async(_func, product_all)
        res.get()
    pool.close()


def run_single_thread(path_instance_data=None,
                      path_results_folder=None,
                      time_limit=100):
    """ 
    Iterates through all problem instances and prints performance profile in results folder without parallellisation 
    """
    for file in os.listdir(path_instance_data):
        instance_name = os.fsdecode(file)
        print(instance_name)  #filename
        if instance_name.endswith(".vrp"):
            for dive in [True, False]:
                for subproblem_type in ["lp", "cspy"]:
                    if subproblem_type == "cspy":
                        cspy = True
                    else:
                        cspy = False
                    for hyper in [True, False]:
                        for pricing_strategy in [
                                "BestPaths", "BestEdges1", "BestEdges2",
                                "Exact"
                        ]:
                            for greedy in [True, False]:

                                data = DataSet(path=path_instance_data,
                                               instance_name=instance_name)

                                table = CsvTableVRPy(
                                    path=path_instance_data,
                                    instance_name=instance_name)

                                prob = VehicleRoutingProblem(
                                    data.G,
                                    load_capacity=data.max_load,
                                    use_hyper_heuristic=hyper)

                                prob.solve(dive=dive,
                                           greedy=greedy,
                                           cspy=cspy,
                                           pricing_strategy=pricing_strategy,
                                           time_limit=5,
                                           compute_runtime=True)

                                table.get_data_from_VRPy_instance(
                                    dive=dive,
                                    cspy=cspy,
                                    pricing_strategy=pricing_strategy,
                                    greedy=greedy,
                                    comp_time=prob.comp_time,
                                    best_value=prob.best_value,
                                    lower_bound=prob._lower_bound[-1],
                                    hyper=hyper)
                                table.write_to_file(
                                    path_results_folder=path_results_folder)

        else:
            continue


def iterate_through_instances(path_instance_data=None,
                              path_results_folder=None,
                              time_limit=100,
                              multi_thread=True):
    """
    Iterates through all problem instances and prints performance profile in results folder using parallellisation
    """
    if not path_instance_data == None:
        path_instance_data = path_instance_data
    else:
        #Run from vrpy
        path_instance_data = "examples/benchmarks/data/cvrp/"
    if multi_thread:
        run_parallel(path_instance_data=path_instance_data,
                     path_results_folder=path_results_folder)
    else:
        run_single_thread(path_instance_data=path_instance_data,
                          path_results_folder=path_results_folder)


""" if __name__ == "__main__":
    #Specify absolute paths
    path_instance_data = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/data/cvrp/'
    path_results_folder = '/mnt/c/Users/Halvardo/Documents/code/vrpy/examples/benchmarks/run/'
    iterate_through_instances(path_instance_data=path_instance_data,
                              path_results_folder=path_results_folder,
                              multi_thread=True) """
