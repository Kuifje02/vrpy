from math import exp, log, sqrt
from time import time
import logging
import bisect

from vrpy.checks import check_seed

logger = logging.getLogger(__name__)


class _HyperHeuristic:
    """
    HyperHeuristic class manages the high-level heuristic strategies
    In charge of:
    - Selection
    - Storing, off_line learning
    - Different move acceptance

    Args:
        heuristic_options (list of str, optional):
            list of pricing strategies to consider.
            Defaults to all of them (see main.solve).
        scaling_factor (float, optional):
            set the evolution vs exploration parameter.
            Defaults to 0.5.
        performance_measure_type (str, optional):
            Sets performance measure
            heuristic_options: "weighted_average", "relative_improvement"
            Defaults to "weighted_average".
        acceptance_type(str):
            Set move acceptance.
            - `accept_all`
            - `table` - measure
            - `ob
            Defaults to "accept_all"
        step (float, optional):
            Adaptive step.
            Defaults to 0.02.
        start_computing_average (int):
            Iteration where average starts being computed.
            Defaults to 1.
        seed (int or numpy.random.RandomState):
            Defaults to None.
    """

    def __init__(
        self,
        heuristic_options=["BestPaths", "BestEdges1", "BestEdges2", "Exact"],
        scaling_factor: float = 0.5,
        performance_measure_type="weighted_average",
        acceptance_type="objective_decrease",
        step=0.1,
        start_computing_average=1,
        seed=None,
    ):
        # Input parameters
        self.heuristic_options = heuristic_options
        self.scaling_factor = scaling_factor
        self.performance_measure_type = performance_measure_type
        self.acceptance_type = acceptance_type
        self.step = step
        self.start_computing_average = start_computing_average
        self.random_state = check_seed(seed)

        # Internal parameters
        self.theta = 1
        self.inf = 1e10
        self.current_objective_value = None
        self.current_heuristic = None
        self.new_objective_value = None
        self.produced_column = None
        self.obj_has_decreased: bool = None

        self.d = 0
        self.d_max = 0
        self.iteration = None
        self.average_runtime = None

        self.iterations = {h: 0 for h in self.heuristic_options}
        self.q = {h: 0 for h in self.heuristic_options}
        self.r = {h: 0 for h in self.heuristic_options}
        self.added_columns = {h: 0 for h in self.heuristic_options}
        self.exp = {h: 0 for h in self.heuristic_options}
        self.heuristic_points = {h: self.inf for h in self.heuristic_options}
        self.objective_decrease = {h: 0 for h in self.heuristic_options}
        self.norm_objective_decrease = {h: 0 for h in self.heuristic_options}
        self.norm_runtime = {h: 0 for h in self.heuristic_options}
        self.last_runtime_dict = {h: 0 for h in self.heuristic_options}

        self.runtime_dist = []
        self.active_columns = {}
        self.total_objective_decrease = 0.0
        # Weights
        # See _update_params_wgtavr for use
        self.weight_col_basic = 0.5
        self.weight_runtime = 0.1
        self.weight_spread = 0.3
        self.weight_obj = 0.05
        self.weight_col_total = 0.05

        # time related parameters
        self.start_time = None
        self.end_time = None
        self.last_runtime = None
        self.time_windows = None

    def init(self, relaxed_cost: float):
        "Set initial parameters"
        self.current_heuristic = "BestPaths"
        self.set_current_objective(relaxed_cost)
        self.end_time = time()

    def set_current_objective(self, objective: float = None):
        "sets current_objective_value"
        self.current_objective_value = objective

    def pick_heuristic(self):
        "Sets the chosen heuristic based on selection points"
        # set performance measure
        if self.performance_measure_type == "relative_improvement":
            # before the number of iterations is high enough
            if self.iteration < self.start_computing_average:
                return self.random_state.choice(self.heuristic_options[0:2])
        elif self.performance_measure_type == "weighted_average":
            pass
        # choose according to MAB
        maxval = max(self.heuristic_points.values())
        best_heuristics = [
            i for i, j in self.heuristic_points.items() if j == maxval
        ]
        if len(best_heuristics) == 1:
            self.current_heuristic = best_heuristics[0]
        else:
            self.current_heuristic = self.random_state.choice(best_heuristics)
        return self.current_heuristic

    def update_scaling_factor(self, no_improvement_count: int,
                              no_improvement_iteration: int):
        """
        Implements Drake et al. (2012)

        Additionally, we change the step to be proportional to the number of
        iterations where there has been improvement.
        no_improvement_count / (current_iteration - last_improvement_iteration)

        The higher the step the more adaptive the algorithm, hence, with the
        revised step (as above), the hyper-heuristic will explore more when
        there
        see: https://link.springer.com/chapter/10.1007/978-3-642-32964-7_31
        """
        # TODO
        # if self.iteration - no_improvement_iteration > 0:
        #     self.step = no_improvement_count / (self.iteration -
        #                                         no_improvement_iteration)
        if self.obj_has_decreased and self.produced_column:
            self.theta = 0.99
        else:
            self.theta = max(self.theta - self.step, self.step)

    def current_performance(
        self,
        new_objective_value: float = None,
        produced_column: bool = None,
        active_columns: dict = None,
    ):
        "Updates the variables at the current iteration"
        self._compute_last_runtime()
        self.iterations[self.current_heuristic] += 1

        # column produced
        self.produced_column = produced_column
        if produced_column:
            self.added_columns[self.current_heuristic] += 1

        # objective function measure
        self.obj_has_decreased = self.current_objective_value - new_objective_value > 0

        if self.performance_measure_type == "relative_improvement":
            self._current_performance_relimp(produced_column=produced_column)

        elif self.performance_measure_type == "weighted_average":
            self._current_performance_wgtavr(
                active_columns=active_columns,
                new_objective_value=new_objective_value)
        else:
            raise ValueError("performence_measure not set correctly!")
        self.set_current_objective(objective=new_objective_value)

    def move_acceptance(self):
        """
        Adds new improvement to the improvements dict and applies the move
        acceptance step

        Args:
            new_objective_value (float): new_objective_value. Defaults to None.
        """
        update = True
        if self.acceptance_type == "accept_all":
            return update
        elif self.acceptance_type == "table":
            if not self.obj_has_decreased:
                update = self.random_state.uniform(0, 1) < 0.5 * exp(self.d)
        elif self.acceptance_type == "objective_threshold":
            if self.obj_has_decreased:
                return True
            return self.random_state.uniform(0, 1) < exp(self.d)
        return update

    def reward(self, y, stagnated=True):
        "Modify the improvement"
        # if there is stagnation, set improvement to small number
        x = min(0.1 * self.d_max, y) if stagnated else y
        if self.obj_has_decreased and self.produced_column and y > 0:
            x *= 1.5
        elif y <= 0:
            pass
        elif self.obj_has_decreased or self.produced_column:
            x *= 1.2
        else:
            x *= 0.9
        return x

    def update_parameters(self, iteration: int, no_improvement_count: int,
                          no_improvement_iteration: int):
        "Updates the high-level parameters"
        # measure time and add to weighted average
        self.iteration = iteration
        self.update_scaling_factor(no_improvement_count,
                                   no_improvement_iteration)
        # compute average of runtimes
        if self.performance_measure_type == "relative_improvement":
            self._update_params_relimp()
        elif self.performance_measure_type == "weighted_average":
            self._update_params_wgtavr()
        else:
            logger.debug("heuristic parameters not updated")

    def _compute_last_runtime(self):
        # computes last time
        self.start_time = self.end_time
        self.end_time = time()
        self.last_runtime = self.end_time - self.start_time
        self.last_runtime_dict[self.current_heuristic] = self.last_runtime

    def _current_performance_relimp(self, produced_column: bool = False):
        #   time measure
        if self.iteration > self.start_computing_average + 1:
            self.d = max((self.average_runtime - self.last_runtime) /
                         self.average_runtime * 100, 0)
            logger.debug("Resolve count %s, improvement %s", produced_column,
                         self.d)
            if self.d > self.d_max:
                self.d_max = self.d
                logger.debug(
                    "Column produced, average runtime %s and last runtime %s",
                    self.average_runtime, self.last_runtime)
            else:
                self.d = 0

    def _current_performance_wgtavr(self,
                                    new_objective_value: float = None,
                                    active_columns: dict = None):
        self.active_columns = active_columns
        # insert new runtime into sorted list
        bisect.insort(self.runtime_dist, self.last_runtime)
        self.objective_decrease[self.current_heuristic] += max(
            self.current_objective_value - new_objective_value, 0)
        self.total_objective_decrease += max(
            self.current_objective_value - new_objective_value, 0)
        # update quality values
        for heuristic in self.heuristic_options:
            if self.iterations[heuristic] > 0:
                self._update_exp(heuristic)
                index = bisect.bisect(self.runtime_dist,
                                      self.last_runtime_dict[heuristic])
                self.norm_runtime[heuristic] = (len(self.runtime_dist) -
                                                index) / len(self.runtime_dist)
                if self.total_objective_decrease > 0:
                    self.norm_objective_decrease[heuristic] = (
                        self.objective_decrease[heuristic] /
                        self.total_objective_decrease)

    def _update_params_relimp(self):
        "Updates params for relative improvements performance measure"
        if self.iteration <= self.start_computing_average:
            return
        reduced_n = (self.iteration - self.start_computing_average) % 10
        if reduced_n == 0:
            self.average_runtime = self.last_runtime
        else:
            self.average_runtime = (self.average_runtime * (reduced_n - 1) /
                                    (reduced_n) + 1 /
                                    (reduced_n) * self.last_runtime)
        heuristic = self.current_heuristic
        # store old values
        old_q = self.q[heuristic]
        old_n = self.iterations[heuristic] - 1
        stagnated = old_q == 0 and old_n > 3
        # average of improvements
        self.r[heuristic] = self.r[heuristic] * old_n / (old_n + 1) + 1 / (
            old_n + 1) * self.reward(self.d, stagnated=stagnated)
        self.q[heuristic] = (old_q + self.r[heuristic]) / (old_n + 1)
        # compute heuristic points MAB-style
        for heuristic in self.heuristic_options:
            if self.iterations[heuristic] != 0:
                self._update_exp(heuristic)
                self.heuristic_points[heuristic] = (
                    self.theta * self.q[heuristic] +
                    self.scaling_factor * self.exp[heuristic])

    def _update_exp(self, heuristic):
        self.exp[heuristic] = sqrt(2 * log(sum(self.iterations.values())) /
                                   self.iterations[heuristic])

    def _update_params_wgtavr(self):
        "Updates params for Weighted average performance measure"
        sum_exp = sum(self.exp.values())
        active = sum(self.active_columns.values())
        for heuristic in self.heuristic_options:
            # if heuristic has not been applied, let it be self.inf
            if self.iterations[heuristic] > 0:
                active_i = self.active_columns[heuristic]
                total_added = self.added_columns[heuristic]
                norm_runtime = self.norm_runtime[heuristic]
                norm_spread = 0
                if sum_exp != 0:
                    norm_spread = self.exp[heuristic] / sum_exp
                self.q[heuristic] = (
                    self.weight_col_basic * active_i / active +
                    self.weight_runtime * norm_runtime +
                    self.weight_obj * self.norm_objective_decrease[heuristic] +
                    self.weight_col_total * active_i / total_added)
                self.heuristic_points[heuristic] = self.theta * self.q[
                    heuristic] + self.weight_spread * norm_spread * (1 -
                                                                     self.theta)
