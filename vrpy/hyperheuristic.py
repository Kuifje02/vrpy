from random import uniform, choice
from math import exp, log, sqrt
from time import time
import json
#from .main import VehicleRoutingProblem
"""
TODO: 
    - Bruke reduced cost på en måte! (Multiobjective optimisiation) GO R
    - Gi muligheten for å velge en spesifikk heurestikk R, kan gjøre bedre
    - Straffe heurestikken hvis det ikke er forbedring, ved å øke n[i]
    - Det sto noe i den andre om rank based move acceptance, dette bør sjekkes ut fordi vi bryr oss om hvorvidt nye kolonner er funnet, men ikke om verdier!
"""
# tre oppgaver: learning R for now, update data structures R , and change the punishment criterium Lets go!

# påstand4 (big step), hva med å ordne heurestikkene i en prioritetskø?

#Oppgaver
# Finn en måte å sammenlikne resultatet av metaheurestikken på de ulike instancene!
# Finn ut best måte å teste performance av metaheurestikken
# Kjøre performance profileren på en rekke instances, basically!
# ting jeg setter: move_acceptance
# ting som jeg vil ha med.
# reject list, n_list,
# Sammenlikne Kjøretid i move_acceptance criteria
# ta stilling til om jeg vil kjøre på

# SLITEN:
#navnendringer:
"hyperparams"
#sette inn types i metodene


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
    def __init__(self,
                 poolsize: int = 4,
                 start_heur: int = 0,
                 scaling_factor: float = 0.01,
                 offline_learning: bool = False):

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
        self.d = 0

        #Consider setting to zero
        self.heuristic_points = [self.inf] * poolsize
        self.improvements = {}
        for element in range(poolsize):
            self.improvements[element] = {}

        #consider
        self.current_heuristic = start_heur
        self.loaded_parameters = {}

        #total time
        self.timestart = None
        self.timeend = None
        self.time_windows = None
        self.pos_reduced_cost = None
        self.reject_list = [0, 0, 0, 0]
        self.total_n = 0
        self.start_computing_average = 3
        self.last_runtime = None
        self.average_runtime = 0

    def set_current_objective(self, objective: float = None):
        """
        sets current_objective_value
        """
        self.current_objective_value = objective

    def pick_heurestic(self, heuristic: int = None):
        """
        Sets the chosen heuristic based on heuristic points
        """

        #force a particular heuristic
        if not heuristic == None:
            return heuristic

        #before the number of iterations is high enough
        if self.total_n < self.start_computing_average:
            return choice(self.pool)

        #choose according to MAB
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

    def current_performance(self,
                            new_objective_value: float = None,
                            pos_reduced_cost: bool = None):
        """Updates the variables relevant for the last iteration

        Args:
            new_objective_value (float, optional): [description]. Defaults to None.
            pos_reduced_cost (bool, optional): [description]. Defaults to None.
        """
        #   computes last time
        if self.total_n == 0:
            self.timeend = time()
        else:
            self.timestart = self.timeend
            self.timeend = time()
            self.last_runtime = self.timeend - self.timestart

        #   objective function measure
        self.pos_reduced_cost = pos_reduced_cost
        self.obj_decrease = self.current_objective_value - new_objective_value > 0

        #   time measure
        if self.total_n > self.start_computing_average + 1:  #problem er at vi beregner ny average etter d.
            self.d = max((self.average_runtime - self.last_runtime) /
                         self.average_runtime * 100, 0)

        #problemer:
        #   n burde være null, nei
        #

        #   self.average_runtime =

        # compute weighted average runtime
        # options: let every heuristic run once

    def move_acceptance(self):
        """
        Adds new improvement to the improvements dict and applies the move acceptance step

        Args:
            new_objective_value (float): new_objective_value. Defaults to None.

        Returns:
            (bool): if the move is accepted or not
        """
        self.move_acceptance == "Accept all"
        update = True

        # different move acceptences
        if self.move_acceptance == "Accept all":
            return True

        elif self.move_acceptance == "Table":  #fikse d her
            if self.obj_decrease and self.pos_reduced_cost:
                pass
            elif self.obj_decrease and not self.pos_reduced_cost:
                update = uniform(0, 1) < 0.5 * exp(self.d)
            elif not self.obj_decrease and self.pos_reduced_cost:
                update = uniform(0, 1) < 0.5 * exp(self.d)
            else:
                update = uniform(0,
                                 1) < 0.1 * exp(self.d)  #både punishe og øke

        elif self.move_acceptance == "objective_threshold":
            if self.obj_decrease:
                return True
            else:
                return uniform(0, 1) < exp(self.d)

        #updates list of rejected heuristics (UNUSED)
        if not update:
            self.reject_list[self.current_heuristic] += 1

        return update

    def reward(self, y):
        x = y  #care?
        if self.obj_decrease:
            x /= 2
        elif self.pos_reduced_cost:
            x /= 2
        return x

    def update_parameters(self):
        """Updates the high-level parameters
        """
        # check if above the weighted average or not performance thing -> as with MAB
        # measure time and add to weighted average
        # have the two boolean functions which affects the r-parameter, set it as below.

        i = self.current_heuristic

        #compute average of runtimes
        self.total_n += 1

        if self.total_n > self.start_computing_average:
            reduced_n = self.total_n - self.start_computing_average
            self.average_runtime = self.average_runtime * (reduced_n - 1) / (
                reduced_n) + 1 / (reduced_n) * self.last_runtime

            #store old values
            old_q = self.q[i]
            old_n = self.n[i]

            #update new values
            self.n[
                i] += 1  #ta hensyn til at vi ønsker randomly chosen de første fire
            self.r[i] = self.r[i] * old_n / (old_n + 1) + 1 / (
                old_n + 1) * self.reward(self.d)
            """TODO: implement operations depending on no_improvement and bad_column
            """
            self.q[i] = (old_q + self.r[i]) / (old_n + 1)

            #compute heuristic points MAB-style
            for j in range(len(self.pool)):
                if not self.n[j] == 0:
                    self.heuristic_points[
                        j] = self.q[j] + self.scaling_factor * sqrt(
                            2 * log(sum(self.n)) /
                            self.n[j])  # consider adaptive selection
        else:
            pass

    def write_to_file(self):
        dumped_parameters = {
            "r": self.r,
            "q": self.q,
            "n": self.n
        }  #consider adding more
        dumpobj = json.dumps(dumped_parameters)
        f = open("hyper_heuristic_parameters.json", "w")
        f.write(dumpobj)
        f.close()
        # should learning be it's own method?
        # we are adding new columns as we go along, but can we compare the solutions when they are at different subproblems?
        # store the data somewhere!

    def read_from_file(self, filename: str = ""):
        try:
            self.loaded_parameters = json.loads(filename)
            self.q = self.loaded_parameters["q"]
            self.r = self.loaded_parameters["r"]
            self.n = self.loaded_parameters["n"]
        except:
            print("Failed to load")
            pass

        # Problemer:
        # hvordan starte prosessen hvis man laster data fra fil -> la en gå metoden. initialiser og så sett alle verdiene. -> så velg. #TODO i main og her.
        # hvordan holde koll på probleminstanser? Ikke oppdatere dictionarien hvis man identifiserer med samme problem? -> lagre en dictionary i en fil med data fra en specific instance
        #
