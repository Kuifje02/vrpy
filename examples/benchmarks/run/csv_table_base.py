import csv
import sys
import os
import time

from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class CsvTableBase:
    """
    Base class for CSVTable.
    Args:
        path (string): Path to instance data
        instance_name (string): Name of the test instance
        comp_time (float): Computation time
        upper_bound(float): Integer optimal value
        lower_bound(float): Relaxed optimal value
        integrality_gap(float): Integer relaxed discrepency
        pricing_strategy(string): Heuristic strategy
        subproblem_type(string): Subproblem type
        dive (bool): Diving heuristic
    Methods:
        Write to file: Creates a results folder in the current directory and writes the relevant data to a file specified by instance name.
    """
    def __init__(self,
                 path=None,
                 instance_name=None,
                 instance_type=None,
                 comp_time=None,
                 upper_bound=None,
                 lower_bound=None,
                 integrality_gap=None,
                 optimality_gap=None,
                 optimal=None,
                 pricing_strategy=None,
                 subproblem_type=None,
                 dive=None,
                 best_known_solution=None):
        self.path = path
        self.instance_name = instance_name if not instance_name.endswith(
            '.csv') else instance_name[:-4]
        self.instance_type = instance_type

        self.best_known_solution = best_known_solution

        self.dive = dive
        self.pricing_strategy = pricing_strategy
        self.subproblem_type = subproblem_type

        self.comp_time = comp_time
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.integrality_gap = integrality_gap
        self.optimality_gap = optimality_gap
        self.optimal = optimal

    def write_to_file(self, path=""):
        cdir = os.path.dirname(__file__)
        total_path = cdir + "/results"

        try:
            os.makedirs(total_path)
        except:
            pass

        os.chdir(total_path)

        #if any is none, print error message

        if os.path.isfile("./" + self.instance_name + ".csv"):
            mode = 'a'
        else:
            mode = 'w'

        with open(self.instance_name + ".csv", mode, newline='') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=[
                                        "Instance", "Pricing strategy",
                                        "Subproblem type", "Dived", "Runtime",
                                        "Integrality gap", "Optimality gap",
                                        "Optimal"
                                    ])
            if mode == 'w':
                writer.writeheader()
            writer.writerow({
                "Instance": self.instance_name,
                "Pricing strategy": self.pricing_strategy,
                "Subproblem type": self.subproblem_type,
                "Dived": self.dive,
                "Runtime": self.comp_time,
                "Integrality gap": self.integrality_gap,
                "Optimality gap": self.optimality_gap,
                "Optimal": self.optimal
            })
        csv_file.close()
