from random import uniform, choice
from math import exp, log, sqrt
from time import time
import json
#from .main import VehicleRoutingProblem
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
"""
TODO: 
    #Oppgaver
# Kjøre performance profileren på en rekke instances, basically!
# Fikse i 1) main 2) hyper 3) csv_writer
# Finne noen gode instancer å se på
# Resette average runtime, vurdere -> raskere enn previous search markov chain

# Så kan vi se mer på move_acceptance

# SLITEN:
# sortere variablene
# åpne for muligheten å velge en spesifikk heurestikk
    - Det sto noe i den andre om rank based move acceptance, dette bør sjekkes ut fordi vi bryr oss om hvorvidt nye kolonner er funnet, men ikke om verdier! (kanskje)
# ordne modulo greiene 

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
    def __init__(self,
                 poolsize: int = 4,
                 start_heur: int = 0,
                 scaling_factor: float = 0.5,
                 offline_learning: bool = False):

        #params
        self.scaling_factor = scaling_factor
        self.theta = 1
        #self.decay_factor = None

        #self.time_limit = None
        self.current_objective_value = None
        self.new_objective_value = None
        self.pos_reduced_cost = None  #ikke egentlig positive reduce cost at this point

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
        self.exp_list = [0] * poolsize
        self.d = 0
        self.d_max = 0
        self.total_n = 0
        self.average_runtime = 0

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
        self.last_runtime = None
        self.time_windows = None
        self.start_computing_average = 1
        self.reject_list = [0, 0, 0, 0]

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

    def update_scaling_factor(self):
        if self.obj_decrease and self.d > 0 and self.pos_reduced_cost:
            self.theta = 0.99
        else:
            self.theta = max(self.theta - 0.1, 0.1)

    def current_performance(self,
                            new_objective_value: float = None,
                            pos_reduced_cost: bool = None,
                            resolve_count=None):
        """Updates the variables relevant for the last iteration
        TODO: Consider changing self.d somehow to reflect not just improvements. One fix is normalisation

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

        #   incorporate resolve count

        #   time measure
        if self.total_n > self.start_computing_average + 1:  #problem er at vi beregner ny average etter d.
            self.d = (self.average_runtime -
                      self.last_runtime) / self.average_runtime * 100
            logger.info("Resolve count %s, improvement %s" %
                        (resolve_count, self.d))
            if self.d > self.d_max:
                self.d_max = self.d

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

    def reward(self, y, lower_bound=True):
        """
        Måte 1: multiplicative reward, prob 0 -> 0 
        Måte 2: minste terskel
        Mate 3: Med negative improvements, ikke forverr 
        TODO: implementere pos reduced cost (alltid true)
        """
        # Trøstepremie
        if lower_bound:
            x = min(0.1 * self.d_max, y)
        else:
            x = y

        #positive improvement
        if y > 0:
            if self.obj_decrease and self.pos_reduced_cost:
                x *= 1.5
            elif self.obj_decrease and not self.pos_reduced_cost:
                x *= 1.2
            elif not self.obj_decrease and self.pos_reduced_cost:
                x *= 1.2
            else:
                x *= 0.9
        #negative improvement
        else:
            if self.obj_decrease and self.pos_reduced_cost:
                x /= 1.5
            elif self.obj_decrease and not self.pos_reduced_cost:
                x /= 1.2
            elif not self.obj_decrease and self.pos_reduced_cost:
                x /= 1.2
            else:
                x /= 0.9

        return x

    def update_parameters(self):
        """Updates the high-level parameters
        """
        # measure time and add to weighted average

        i = self.current_heuristic

        self.update_scaling_factor()

        #compute average of runtimes
        self.total_n += 1

        if self.total_n > self.start_computing_average:
            reduced_n = (self.total_n - self.start_computing_average) % 10
            if reduced_n == 0:
                self.average_runtime = self.last_runtime
            else:
                self.average_runtime = self.average_runtime * (
                    reduced_n -
                    1) / (reduced_n) + 1 / (reduced_n) * self.last_runtime

            #store old values
            old_q = self.q[i]
            old_n = self.n[i]

            #frozen TRUE
            frozen = (old_q == 0 and old_n > 3)

            #update new values
            self.n[
                i] += 1  #ta hensyn til at vi ønsker randomly chosen de første fire

            #tail heavy approach
            self.r[i] = self.r[i] * old_n / (old_n + 1) + 1 / (
                old_n + 1) * self.reward(self.d, lower_bound=frozen)
            #reflets the current state of the search
            #self.r[i] = self.reward(self.d)
            """TODO: implement operations depending on no_improvement and bad_column
            """

            self.q[i] = (old_q + self.r[i]) / (old_n + 1)

            #compute heuristic points MAB-style
            for j in range(len(self.pool)):
                if not self.n[j] == 0:
                    self.exp_list[j] = sqrt(2 * log(sum(self.n)) / self.n[j])
                    self.heuristic_points[
                        j] = self.theta * self.q[j] + self.scaling_factor * (
                            1 - self.theta
                        ) * self.exp_list[j]  # consider adaptive selection
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
