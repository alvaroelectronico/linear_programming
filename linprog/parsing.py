"""Parse human-readable linear programs into standard-form matrices.

A problem is described by:

* ``num_vars`` -- the number of decision variables ``x_1 ... x_n``.
* ``objective`` -- a ``(sense, expression)`` tuple, e.g. ``("max", "3x_1 + 2x_2")``
  where ``sense`` contains ``"max"`` or ``"min"``.
* ``constraints`` -- a list of strings such as ``"2x_1 + 4x_2 >= 80"``. Tokens
  must be single-space separated; each variable term is written ``<coeff>x_<i>``.

This module turns that description into the matrices the solvers operate on,
adding slack and artificial variables as required by the chosen method.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from linprog.fractions_utils import array_to_fraction

SUPPORTED_METHODS = ("simplex", "lemke")


def parse_objective_coefficients(expression: str) -> dict[int, Fraction]:
    """Map each variable index (0-based) to its objective coefficient.

    Tokens without an underscore (operators, stray terms) are ignored, matching
    the lenient behaviour expected by the textbook problems this tool targets.
    """
    coefficients: dict[int, Fraction] = {}
    tokens = expression.split()
    for i, token in enumerate(tokens):
        if "_" not in token:
            continue
        coeff, index = token.split("_")
        value = Fraction(coeff[:-1])
        if tokens[i - 1] == "-":
            value = -value
        coefficients[int(index) - 1] = value
    return coefficients


@dataclass
class StandardForm:
    """Standard-form data shared by every solver backend.

    Attributes mirror the textbook notation: ``A`` is the constraint matrix
    (including slack/artificial columns), ``b`` the right-hand side, ``c1`` the
    phase-1 objective coefficients and ``c2`` the original (phase-2) objective
    coefficients. ``coeff_matrix`` is the initial simplex tableau (objective row
    zeroed); solvers mutate a copy of it while pivoting.
    """

    num_vars: int
    num_slack_vars: int
    num_artificial_vars: int
    objective_sense: str
    objective_expr: str
    constraints: list[str]
    constraint_senses: list[str]
    A: np.ndarray
    b: np.ndarray
    c1: np.ndarray
    c2: np.ndarray
    var_names: list[str]
    slack_rows: list[int]
    artificial_rows: list[int]
    coeff_matrix: list[list[Fraction]]

    @property
    def total_vars(self) -> int:
        return self.num_vars + self.num_slack_vars + self.num_artificial_vars


def _count_auxiliary_vars(constraints, method) -> tuple[list[str], int, int]:
    """Detect each constraint's sense and count slack/artificial variables."""
    senses = [""] * len(constraints)
    num_slack = 0
    num_artificial = 0
    for i, expression in enumerate(constraints):
        if "<=" in expression:
            senses[i] = "<="
            num_slack += 1
        elif ">=" in expression:
            senses[i] = ">="
            num_slack += 1
            if method == "simplex":
                num_artificial += 1
        elif "=" in expression:
            senses[i] = "="
            if method == "simplex":
                num_artificial += 1
    return senses, num_slack, num_artificial


def _variable_names(num_vars, slack_rows, artificial_rows) -> list[str]:
    """Build display names: ``x_i`` originals, ``h_i`` slacks, ``a_i`` artificials."""
    names = [f"x_{i}" for i in range(1, num_vars + 1)]
    names += [f"h_{row}" for row in slack_rows]
    names += [f"a_{row}" for row in artificial_rows]
    return names


def build_standard_form(num_vars, constraints, objective_function, method="simplex"):
    """Parse a problem description into a :class:`StandardForm` instance."""
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Method {method!r} is not supported")

    objective_sense, objective_expr = objective_function
    senses, num_slack, num_artificial = _count_auxiliary_vars(constraints, method)
    total_vars = num_vars + num_slack + num_artificial

    # Tableau: one row per constraint plus the objective row (index 0, zeroed),
    # and one column per variable plus the right-hand side.
    coeff_matrix = [
        [Fraction(0) for _ in range(total_vars + 1)]
        for _ in range(len(constraints) + 1)
    ]

    first_slack_index = num_vars
    first_artificial_index = num_vars + num_slack
    slack_index = first_slack_index
    artificial_index = first_artificial_index
    slack_rows: list[int] = []
    artificial_rows: list[int] = []

    for i in range(1, len(constraints) + 1):
        tokens = constraints[i - 1].split(" ")
        for j, token in enumerate(tokens):
            if "_" in token:
                coeff, index = token.split("_")
                value = Fraction(coeff[:-1]).limit_denominator()
                if tokens[j - 1] == "-":
                    value = -value
                coeff_matrix[i][int(index) - 1] = value
            elif token == "<=":
                coeff_matrix[i][slack_index] = Fraction(1)
                slack_index += 1
                slack_rows.append(i)
            elif token == ">=":
                coeff_matrix[i][slack_index] = Fraction(-1)
                slack_index += 1
                slack_rows.append(i)
                if method == "simplex":
                    coeff_matrix[i][artificial_index] = Fraction(1)
                    artificial_index += 1
                    artificial_rows.append(i)
            elif token == "=":
                if method != "simplex":
                    raise ValueError(
                        "Equality constraints are not supported by Lemke's method"
                    )
                coeff_matrix[i][artificial_index] = Fraction(1)
                artificial_index += 1
                artificial_rows.append(i)
        coeff_matrix[i][-1] = Fraction(tokens[-1] + "/1")

    # Phase-1 objective: 0 for structural/slack vars, -1 for each artificial.
    c1 = [Fraction(0)] * (num_vars + num_slack) + [Fraction(-1)] * num_artificial

    # Phase-2 (original) objective, placed across the full variable width.
    c2 = [Fraction(0)] * total_vars
    for index, value in parse_objective_coefficients(objective_expr).items():
        c2[index] = value

    c1 = array_to_fraction(np.array(c1).reshape(-1, 1))
    c2 = array_to_fraction(np.array(c2).reshape(-1, 1))
    if method == "lemke" and "min" in objective_sense:
        c2 = -c2

    A = array_to_fraction(
        np.array([row[:-1] for row in coeff_matrix[1:]])
    )
    b = array_to_fraction(
        np.array([row[-1] for row in coeff_matrix[1:]]).reshape(-1, 1)
    )

    var_names = _variable_names(num_vars, slack_rows, artificial_rows)

    return StandardForm(
        num_vars=num_vars,
        num_slack_vars=num_slack,
        num_artificial_vars=num_artificial,
        objective_sense=objective_sense,
        objective_expr=objective_expr,
        constraints=list(constraints),
        constraint_senses=senses,
        A=A,
        b=b,
        c1=c1,
        c2=c2,
        var_names=var_names,
        slack_rows=slack_rows,
        artificial_rows=artificial_rows,
        coeff_matrix=coeff_matrix,
    )
