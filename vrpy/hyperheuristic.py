from random import uniform, choice
from math import exp, log, sqrt
#from .main import VehicleRoutingProblem
"""
TODO: 
    - Bruke reduced cost på en måte! (Multiobjective optimisiation)
    - Gi muligheten for å velge en spesifikk heurestikk
    - Straffe heurestikken hvis det ikke er forbedring, ved å øke n[i]
    - Change the move acceptance
    - Det sto noe i den andre om rank based move acceptance, dette bør sjekkes ut fordi vi bryr oss om hvorvidt nye kolonner er funnet, men ikke om verdier!
"""


class HyperHeuristic:
    """
    HyperHeuristic class manages the high-level heuristic strategies
    Args: 
        scaling_factor (float): 
            parameter deciding the balance between exploration and explotation
        decay_factor (float)
        time_limit (float): 
            total time limit for the algorithm
        current_objective_value (float): 
            the objective value for previous iteration
        new_objective_value (float): 
            the objective value for the current iteration
        inf (float): 
            very large number 
        iteration_counter (int): 
            counts the number of iterations
        initialisation (bool): 
            initialisation parameter 
        heur_names (list, str): 
            names of heurestic strategies 
        pool (list, int: 
            the pool of heurestics, indexed by integers
        q (list, floats): 
            list of accumulative rewards
        r (list, floats): 
            list of average improvements
        n (list, int): 
            list of iteration counters
        heuristic_points (list, floats): 
            list of points for each heurestic at the current timepoint
        improvements (dict, dict, floats):
            a dictionary with keys indexed by heuristics with values equal to dictionaries with rewards
        current_heuristic (int):
            the currently applied heuristic
    """
    def __init__(self, poolsize=4, start_heur=0, scaling_factor=0.01):

        #params
        self.scaling_factor = scaling_factor
        #self.decay_factor = None

        #self.time_limit = None
        self.current_objective_value = None
        self.new_objective_value = None

        self.inf = 1E10

        #consider
        #self.iteration_counter = 0  # maybe one for each heuristic?
        self.initialisation = True

        #high level data
        self.heur_names = ["BestPaths", "BestEdges1", "BestEdges2", "Exact"]
        self.pool = [i for i in range(poolsize)]
        self.q = [0] * poolsize
        self.r = [0] * poolsize
        self.n = [0] * poolsize
        self.heuristic_points = [self.inf] * poolsize
        self.improvements = {}
        for element in range(poolsize):
            self.improvements[element] = {}

        #consider
        self.current_heuristic = start_heur

    def set_current_objective(self, objective=None):
        """
        sets current_objective_value
        """
        self.current_objective_value = objective

    def pick_heurestic(self):
        """
        Sets the chosen heuristic based on heuristic points
        """
        maxval = max(self.heuristic_points)
        best_heuristics = [
            i for i, j in enumerate(self.heuristic_points) if j == maxval
        ]
        if len(best_heuristics) == 1:
            self.current_heuristic = self.pool[best_heuristics[0]]
        else:
            self.current_heuristic = choice(best_heuristics)
            #vil den ikke så og si alltid bare være en?
        return self.current_heuristic

    def move_acceptance(self, new_objective_value=None):
        """
        Adds new improvement to the improvements dict and applies the move acceptance step

        Args:
            new_objective_value (float): new_objective_value. Defaults to None.

        Returns:
            (bool): if the move is accepted or not
        """

        r = (self.current_objective_value -
             new_objective_value) / self.current_objective_value * 100
        if self.current_objective_value > new_objective_value:
            self.improvements[self.current_heuristic][self.n[
                self.current_heuristic]] = r
            self.current_objective_value = new_objective_value
            return True
        else:
            if uniform(0, 1) < exp(r):
                return True
            else:

                return False

    def update_parameters(self):
        """Updates the high-level parameters
        """
        i = self.current_heuristic

        old_q = self.q[i]

        self.n[i] += 1
        self.r[i] = sum(self.improvements[i].values()) / self.n[i]
        self.q[i] = (old_q + self.r[i]) / self.n[i]

        for j in range(len(self.pool)):
            if not self.n[j] == 0:
                self.heuristic_points[
                    j] = self.q[j] + self.scaling_factor * sqrt(
                        2 * log(sum(self.n)) / self.n[j])

    def learning(self):
        # should learning be it's own method?
        # we are adding new columns as we go along, but can we compare the solutions when they are at different subproblems?
        # store the data somewhere!
        return
