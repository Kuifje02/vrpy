import sys
import time
from .csv_table_base import CsvTableBase


class CsvTableVRPy(CsvTableBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write_to_file(self, path_to):
        super().write_to_file(path_to=path_to)

    def _find_optimal(self):
        if self.instance_type == "augerat":
            with open(self.path + self.instance_name, 'r') as fp:
                fp.readline()
                beststring = (str(fp.readline())[:-2]).split()[-1]
                self.best_known_solution = int(beststring)
            fp.close()
        if self.instance_type == "solomon":
            self.best_known_solution = None

        if self.instance_type == "cordeau":
            self.best_known_solution = None

    def get_data_from_VRPy_instance(self,
                                    best_known_solution=None,
                                    dive=None,
                                    pricing_strategy=None,
                                    best_value=None,
                                    lower_bound=None,
                                    comp_time=None,
                                    cspy=None,
                                    greedy=None):

        if best_known_solution is None:
            self._find_optimal()
        else:
            self.best_known_solution = best_known_solution

        self.dive = dive if not dive is None else False
        self.pricing_strategy = pricing_strategy
        self.subproblem_type = "cspy" if cspy else "lp"

        self.comp_time = comp_time
        self.integrality_gap = (self.upper_bound -
                                self.lower_bound) / self.lower_bound * 100

        if not self.best_known_solution is None:
            self.optimality_gap = (self.upper_bound - self.best_known_solution
                                   ) / self.best_known_solution * 100
            self.optimal = (self.optimality_gap == 0)
        else:
            self.optimality_gap = "Unknown"
            self.optimal = "Unknown"

    """ def get_data_from_VRPy_instance(self,
                                    prob=None,
                                    best_known_solution=None,
                                    subproblem_type=None,
                                    dive=None,
                                    pricing_strategy=None,
                                    *args,
                                    **kwargs):

        time1 = time.time()
        prob.solve(**kwargs, dive=dive)
        time2 = time.time()

        if best_known_solution is None:
            self._find_optimal()
        else:
            self.best_known_solution = best_known_solution

        self.dive = dive if not dive is None else False
        self.pricing_strategy = pricing_strategy
        self.subproblem_type = subproblem_type

        self.comp_time = time2 - time1
        self.upper_bound = prob.best_value
        self.lower_bound = prob._lower_bound[-1]
        self.integrality_gap = (self.upper_bound -
                                self.lower_bound) / self.lower_bound * 100

        if not self.best_known_solution is None:
            self.optimality_gap = (self.upper_bound - self.best_known_solution
                                   ) / self.best_known_solution * 100
            self.optimal = (self.optimality_gap == 0)
        else:
            self.optimality_gap = "Unknown"
            self.optimal = "Unknown" """
