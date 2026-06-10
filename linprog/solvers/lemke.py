"""Lemke's complementary-pivot method with exact rational arithmetic.

Lemke's method here solves an LP whose objective is already in the right sign
convention (coefficients non-positive for a max problem, non-negative for a min
problem). Equality constraints are not supported; see :mod:`linprog.parsing`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from warnings import warn

from linprog.parsing import StandardForm, parse_objective_coefficients
from linprog.solvers._pivot import (
    argmin,
    clear_pivot_column,
    normalize_pivot_row,
)


@dataclass
class LemkeResult:
    bases: list[list[int]]
    optimal_base: list[int]
    solution: dict[str, Fraction]
    objective_value: Fraction


class Lemke:
    def __init__(self, standard_form: StandardForm):
        self.sf = standard_form
        self.tableau = [row[:] for row in standard_form.coeff_matrix]
        self.basic_vars: list[int] = list(range(standard_form.num_vars, standard_form.total_vars))
        self.bases: list[list[int]] = []

    def solve(self) -> LemkeResult:
        self._reset_objective_row()
        self._check_objective_sign()
        self._flip_geq_constraints()

        self._record_base()
        rhs = self._rhs_column()
        key_row = argmin(rhs) + 1
        while any(value < 0 for value in rhs):
            key_column = self._entering_column(key_row)
            if key_column == -1:
                raise ValueError("Infeasible problem")
            self._pivot(key_column, key_row)
            rhs = self._rhs_column()
            key_row = argmin(rhs) + 1
            self._record_base()

        solution = self._read_solution()
        return LemkeResult(
            bases=self.bases,
            optimal_base=self.bases[-1],
            solution=solution,
            objective_value=self.tableau[0][-1],
        )

    def _record_base(self) -> None:
        self.bases.append([int(v) for v in self.basic_vars])

    def _rhs_column(self) -> list[Fraction]:
        return [row[-1] for row in self.tableau[1:]]

    def _reset_objective_row(self) -> None:
        self.tableau[0] = [Fraction(0)] * (self.sf.total_vars + 1)
        for index, value in parse_objective_coefficients(self.sf.objective_expr).items():
            self.tableau[0][index] = value

    def _check_objective_sign(self) -> None:
        sense = self.sf.objective_sense
        if "max" in sense:
            if any(value > 0 for value in self.tableau[0]):
                raise ValueError("Objective to be maximized has a coefficient > 0")
        elif "min" in sense:
            if any(value < 0 for value in self.tableau[0]):
                raise ValueError("Objective to be minimized has a coefficient < 0")
            self.tableau[0] = [-value for value in self.tableau[0]]

    def _flip_geq_constraints(self) -> None:
        for j, sense in enumerate(self.sf.constraint_senses):
            if sense == ">=":
                self.tableau[j + 1] = [-value for value in self.tableau[j + 1]]

    def _entering_column(self, key_row: int) -> int:
        """Pick the entering column by Lemke's ratio test on negative entries."""
        min_val = float("inf")
        min_col = 0
        for j in range(self.sf.total_vars):
            if self.tableau[key_row][j] < 0:
                ratio = self.tableau[0][j] / self.tableau[key_row][j]
                if ratio < min_val:
                    min_val = ratio
                    min_col = j
        if min_val == float("inf"):
            warn("Unbounded problem")
            return -1
        if min_val == 0:
            warn("Multiple optima")
        return min_col

    def _pivot(self, key_column: int, key_row: int) -> None:
        self.basic_vars[key_row - 1] = key_column
        pivot = self.tableau[key_row][key_column]
        normalize_pivot_row(self.tableau, key_row, pivot)
        clear_pivot_column(self.tableau, key_column, key_row)

    def _read_solution(self) -> dict[str, Fraction]:
        solution: dict[str, Fraction] = {}
        for i, var in enumerate(self.basic_vars):
            if var < self.sf.num_vars:
                solution[f"x_{var + 1}"] = self.tableau[i + 1][-1]
        for i in range(self.sf.num_vars):
            if i not in self.basic_vars:
                solution[f"x_{i + 1}"] = Fraction(0)
        return solution
