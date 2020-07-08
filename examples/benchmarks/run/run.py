#!/usr/bin/env python

from networkx import relabel_nodes, DiGraph
import numpy as np
from pandas import read_csv
import sys
import os
import time

from itertools import product
from multiprocessing import Pool

from examples.benchmarks.cvrp_augerat import DataSet


def _func(input_tuple):
    dive, greedy, cspy, pricing_strategy, path, instance_name = input_tuple
    data = DataSet(path=path, instance_name=instance_name)
    data.solve(dive=dive,
               greedy=greedy,
               cspy=cspy,
               pricing_strategy=pricing_strategy,
               time_limit=100)
    return


def run_parallel(path=None, instance_name=None):
    product_all = list(
        product(
            [True, False],  # dive
            [True, False],  # greedy
            [True, False],  # cspy
            ["BestPaths", "BestEdges1", "BestEdges2", "Exact"],
            [path],
            [instance_name]))
    pool = Pool(processes=4)
    with pool:
        res = pool.map_async(_func, product_all)
        res.get()
    pool.close()


def iterate_through_instances_single_thread(datapath=None, time_limit=100):
    """ 
    Iterates through all problem instances and prints performance profile in results folder without parallellisation 
    """

    if not datapath == None:
        path = datapath
    else:
        path = "/../data/cvrp/"

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


def iterate_through_instances_multi_thread(datapath=None, time_limit=100):
    """
    Iterates through all problem instances and prints performance profile in results folder using parallellisation
    """
    if not datapath == None:
        path = datapath
    else:
        #Run from folder
        path = "/../data/cvrp/"

    for file in os.listdir(path):
        filename = os.fsdecode(file)
        if filename.endswith(".vrp"):
            run_parallel(path=path, instance_name=filename)
        else:
            continue
