"""
File to hold different restricted master heuristics.
Will possible move into a single class after implemnting the algorithm
in issue #60 if there is enough overlap.

Currently implemented is
- Diving heuristic
"""
import logging
from typing import List, Optional

import pulp

logger = logging.getLogger(__name__)


class _DivingHeuristic:
    """Implements diving algorithm with Limited Discrepancy Search
    Parameters as suggested by the authors. This only fixes one column.
    `Sadykov et al. (2019)`_.

    .. _Sadykov et al. (2019): https://pubsonline.informs.org/doi/abs/10.1287/ijoc.2018.0822
    """

    def __init__(self, max_depth: int = 3, max_discrepancy: int = 1):
        self.max_depth = max_depth
        self.max_discrepancy = max_discrepancy
        self.depth = 0
        self.current_node = _LPNode()
        self.tabu_list = []

    def run_dive(self, prob):
        tabu_list = []
        relax = prob.deepcopy()
        # Init current_node
        if self.current_node.parent is None:
            self.current_node.parent = relax
        lp_node = _LPNode(self.current_node)
        constrs = {}
        while self.depth <= self.max_depth and len(tabu_list) < self.max_discrepancy:
            non_integer_vars = [
                var
                for var in relax.variables()
                if abs(var.varValue - round(var.varValue)) != 0
            ]
            # All non-integer variables not already fixed in this or any
            # iteration of the diving heuristic
            vars_to_fix = [
                var
                for var in non_integer_vars
                if var.name not in self.current_node.tabu_list
                and var.name not in tabu_list
            ]
            if vars_to_fix:
                # If non-integer variables not already fixed and
                # max_discrepancy not violated

                var_to_fix = min(
                    vars_to_fix, key=lambda x: abs(x.varValue - round(x.varValue))
                )
                value_to_fix = 1
                value_previous = var_to_fix.varValue

                name_le = "fix_{}_LE".format(var_to_fix.name)
                name_ge = "fix_{}_GE".format(var_to_fix.name)
                constrs[name_le] = pulp.LpConstraint(
                    var_to_fix, pulp.LpConstraintLE, name=name_le, rhs=value_to_fix
                )
                constrs[name_ge] = pulp.LpConstraint(
                    var_to_fix, pulp.LpConstraintGE, name=name_ge, rhs=value_to_fix
                )

                relax += constrs[name_le]  # add <= constraint
                relax += constrs[name_ge]  # add >= constraint
                relax.resolve()
                tabu_list.append(var_to_fix.name)
                self.depth += 1
                # if not optimal status code from :
                # https://github.com/coin-or/pulp/blob/master/pulp/constants.py#L45-L57
                if relax.status == 1:
                    prob.extend(constrs)
                    self.current_node = lp_node
                else:
                    # Backtrack
                    self.current_node = self.current_node.parent
                logger.info(
                    "fixed %s with previous value %s", var_to_fix.name, value_previous
                )

            else:
                break
        self.current_node.tabu_list.extend(tabu_list)  # Update global tabu list


class _LPNode:
    def __init__(self, parent=None, tabu_list=[]):
        self.parent = parent
        self.tabu_list = tabu_list
