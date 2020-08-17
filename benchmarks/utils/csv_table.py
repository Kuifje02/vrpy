from pathlib import Path
from csv import DictWriter
from logging import getLogger

logger = getLogger(__name__)


class CsvTable:
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
                 greedy=None,
                 iterations=None,
                 best_known_solution=None):
        self.path = path
        self.instance_name = instance_name if not instance_name.endswith(
            '.csv') else instance_name[:-4]
        self.instance_type = instance_type
        self.comp_time = comp_time
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.integrality_gap = integrality_gap
        self.optimality_gap = optimality_gap
        self.optimal = optimal
        self.pricing_strategy = pricing_strategy
        self.subproblem_type = subproblem_type
        self.dive = dive
        self.greedy = greedy
        self.iterations = iterations
        self.best_known_solution = best_known_solution

    def from_vrpy_instance(self,
                           prob,
                           output_folder: str = "benchmarks/results/"):
        """
        Create csv table using a `vrpy.VehicleRoutingProblem` instance
        """
        # Extract releavant attributes (most are private)
        self.dive = prob._dive
        self.greedy = prob._greedy
        self.pricing_strategy = prob._pricing_strategy
        self.iterations = prob._iteration
        self.subproblem_type = "cspy" if prob._cspy else "lp"

        self.upper_bound = prob.best_value
        self.lower_bound = prob._lower_bound[-1]

        # Calculate gaps
        if self.iterations > 1:
            self.integrality_gap = (self.upper_bound -
                                    self.lower_bound) / self.lower_bound * 100
        else:
            self.integrality_gap = "Not-valid"

        if self.best_known_solution is not None:
            self.optimality_gap = (self.upper_bound - self.best_known_solution
                                   ) / self.best_known_solution * 100
            self.optimal = (self.optimality_gap == 0)
        else:
            self.optimality_gap = "Unknown"
            self.optimal = "Unknown"

        self.write_to_file(output_folder)

    def write_to_file(self, output_folder: str = "benchmarks/results/"):
        """
        Write to file: Creates a results folder in the current directory
        and writes the relevant data to a file specified by instance name.
        """
        output_folder = Path(output_folder)
        # Create folder if it doesn't already exist
        if not output_folder.exists():
            output_folder.mkdir()

        # Append to file if it already exists
        file_name = self.instance_type + ".csv"
        output_file_path = output_folder / file_name
        mode = 'a' if output_file_path.is_file() else 'w'
        with open(output_file_path, mode, newline='') as csv_file:
            writer = DictWriter(csv_file,
                                fieldnames=[
                                    "Instance", "Pricing strategy",
                                    "Subproblem type", "Dived", "Greedy",
                                    "Runtime", "# of iterations",
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
                "Greedy": self.greedy,
                "Runtime": self.comp_time,
                "# of iterations": self.iterations,
                "Integrality gap": self.integrality_gap,
                "Optimality gap": self.optimality_gap,
                "Optimal": self.optimal
            })
        logger.info("Results saved to %s", output_file_path)
        csv_file.close()

    def get_df(self):
        """TODO: write function to get dataframe with only the stuff we want to
        compare with other solvers. i.e. drop the pricing_strategy, ... """
