"""Two-phase Simplex method with exact rational arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from linprog.parsing import StandardForm
from linprog.solvers._pivot import (
    argmax,
    argmin,
    clear_pivot_column,
    min_ratio_row,
    normalize_pivot_row,
    scale_row,
    sum_rows,
)


@dataclass
class SimplexResult:
    """Outcome of a Simplex run.

    ``bases`` lists the basic-variable index sets visited, in order. The first
    feasible basis (end of phase 1) and the optimal basis are called out
    explicitly. ``solution`` maps ``x_i`` names to their optimal values.
    """

    bases: list[list[int]]
    first_feasible_base: list[int] | None
    optimal_base: list[int] | None
    solution: dict[str, Fraction]
    is_infeasible: bool
    is_unbounded: bool
    objective_value: Fraction | None


class Simplex:
    """Solve a :class:`~linprog.parsing.StandardForm` problem by two phases.

    Phase 1 minimises the sum of artificial variables to find a feasible basis;
    phase 2 then optimises the original objective from that basis.
    """

    def __init__(self, standard_form: StandardForm):
        self.sf = standard_form
        # Work on a copy so the StandardForm tableau stays pristine.
        self.tableau = [row[:] for row in standard_form.coeff_matrix]
        self.basic_vars: list[int] = [0] * len(standard_form.constraints)
        self.bases: list[list[int]] = []
        self.is_unbounded = False

    def solve(self) -> SimplexResult:
        first_feasible_base, is_infeasible = self._phase_one()
        if is_infeasible:
            print("Infeasible problem")
            return SimplexResult(
                bases=self.bases,
                first_feasible_base=None,
                optimal_base=None,
                solution={},
                is_infeasible=True,
                is_unbounded=False,
                objective_value=None,
            )

        solution = self._phase_two()
        if self.is_unbounded:
            print("Unbounded problem")
            return SimplexResult(
                bases=self.bases,
                first_feasible_base=first_feasible_base,
                optimal_base=self.bases[-1],
                solution={},
                is_infeasible=False,
                is_unbounded=True,
                objective_value=None,
            )

        return SimplexResult(
            bases=self.bases,
            first_feasible_base=first_feasible_base,
            optimal_base=self.bases[-1],
            solution=solution,
            is_infeasible=False,
            is_unbounded=False,
            objective_value=self.tableau[0][-1],
        )

    def _record_base(self) -> None:
        self.bases.append([int(v) for v in self.basic_vars])

    def _phase_one(self) -> tuple[list[int], bool]:
        sf = self.sf
        first_artificial = sf.num_vars + sf.num_slack_vars

        # Phase-1 objective row: -1 in each artificial column, then add the
        # artificial constraint rows to price out the starting basis.
        for col in range(first_artificial, len(self.tableau[0]) - 1):
            self.tableau[0][col] = Fraction(-1)
        for row in sf.artificial_rows:
            self.tableau[0] = sum_rows(self.tableau[0], self.tableau[row])

        self._identify_basic_vars()

        key_column = argmax(self.tableau[0][:-1])
        self._record_base()
        while self.tableau[0][key_column] > 0:
            self._pivot(key_column)
            key_column = argmax(self.tableau[0][:-1])
            self._record_base()

        is_infeasible = any(v >= first_artificial for v in self.basic_vars)
        return self.bases[-1], is_infeasible

    def _identify_basic_vars(self) -> None:
        """Set ``basic_vars`` by matching each unit column to its row."""
        for i in range(len(self.basic_vars)):
            unit_column = [Fraction(0)] * len(self.basic_vars)
            unit_column[i] = Fraction(1)
            for j in range(self.sf.total_vars):
                column = [row[j] for row in self.tableau[1:]]
                if column == unit_column:
                    self.basic_vars[i] = j
                    break

    def _phase_two(self) -> dict[str, Fraction]:
        sf = self.sf
        self._reset_objective_row()

        # Price out the current basic variables so their reduced costs are zero.
        for row, column in enumerate(self.basic_vars):
            if self.tableau[0][column] != 0:
                self.tableau[0] = sum_rows(
                    self.tableau[0],
                    scale_row(-self.tableau[0][column], self.tableau[row + 1]),
                )

        eligible = sf.num_vars + sf.num_slack_vars  # artificials are not eligible
        key_column = self._entering_column(eligible)
        while self._improves(key_column):
            key_row = min_ratio_row(self.tableau, key_column)
            if key_row == -1:  # no leaving variable -> objective is unbounded
                self.is_unbounded = True
                return {}
            self._pivot(key_column, key_row)
            key_column = self._entering_column(eligible)
            self._record_base()

        solution = self._read_solution()
        self._warn_if_alternate_optimum()
        return solution

    def _entering_column(self, width: int) -> int:
        objective_row = self.tableau[0][:width]
        if "max" in self.sf.objective_sense.lower():
            return argmax(objective_row)
        return argmin(objective_row)

    def _improves(self, key_column: int) -> bool:
        if "max" in self.sf.objective_sense.lower():
            return self.tableau[0][key_column] > 0
        return self.tableau[0][key_column] < 0

    def _reset_objective_row(self) -> None:
        self.tableau[0] = list(self.sf.objective_coeffs) + [Fraction(0)]

    def _pivot(self, key_column: int, key_row: int | None = None) -> None:
        if key_row is None:
            key_row = min_ratio_row(self.tableau, key_column)
        self.basic_vars[key_row - 1] = key_column
        pivot = self.tableau[key_row][key_column]
        normalize_pivot_row(self.tableau, key_row, pivot)
        clear_pivot_column(self.tableau, key_column, key_row)

    def _read_solution(self) -> dict[str, Fraction]:
        names = self.sf.variables
        solution: dict[str, Fraction] = {}
        for i, var in enumerate(self.basic_vars):
            if var < self.sf.num_vars:
                solution[names[var]] = self.tableau[i + 1][-1]
        for i in range(self.sf.num_vars):
            if i not in self.basic_vars:
                solution[names[i]] = Fraction(0)
        return solution

    def _warn_if_alternate_optimum(self) -> None:
        from warnings import warn

        for i in range(len(self.tableau[0])):
            if self.tableau[0][i] and i not in self.basic_vars:
                warn("Alternate Solution exists")
                break
