import csv
import sys
import os
import time

sys.path.append("../../")
# sys.path.append("../../../cspy")
from vrpy.main import VehicleRoutingProblem

import logging

logger = logging.getLogger(__name__)


class CsvTableBase:
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
        self.instance_name = instance_name
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
            #vurdere formattering
        csv_file.close()