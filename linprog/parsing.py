"""Parse human-readable linear programs into standard-form matrices.

A problem is described by:

* ``objective`` -- a ``(sense, expression)`` tuple, e.g. ``("max", "3x + 2y")``
  where ``sense`` contains ``"max"`` or ``"min"``.
* ``constraints`` -- a list of strings such as ``"2x + 4y >= 80"``.

The parser is deliberately forgiving:

* **Any letter** may be a variable, with an optional numeric subscript:
  ``x``, ``y``, ``z``, ``x1``, ``x_1`` ... The underscore is optional, so
  ``x1`` and ``x_1`` denote the same variable (canonical name ``x_1``).
* **Spaces are optional**, both between terms and around the relation sign:
  ``2x+3y<=10`` parses the same as ``2x + 3y <= 10``.
* **Coefficients may be implicit** (``x`` = 1, ``-y`` = -1) and may be integers,
  decimals or fractions (``2.5x``, ``3/2 y``).
* The **number of variables is inferred** from the text. Variables are ordered
  by first appearance, scanning the objective first and then the constraints.
* Variables and constants may appear on **either side** of a constraint; they
  are normalised so variables sit on the left and the constant on the right.

This module turns that description into the matrices the solvers operate on,
adding slack and artificial variables as required by the chosen method.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from linprog.fractions_utils import array_to_fraction

SUPPORTED_METHODS = ("simplex", "lemke")

# A variable is a single letter with an optional (underscore +) digit subscript.
_VARIABLE = r"[A-Za-z](?:_?\d+)?"
# A numeric coefficient: fraction, decimal or integer.
_NUMBER = r"\d+/\d+|\d+\.\d+|\.\d+|\d+"
# One signed term: sign, optional number, optional '*', optional variable.
_TERM = re.compile(rf"^([+-])({_NUMBER})?\*?({_VARIABLE})?$")
_RELATION = re.compile(r"(<=|>=|=)")


def canonical_var(name: str) -> str:
    """Normalise a variable name so ``x1`` and ``x_1`` map to ``x_1``."""
    letter, digits = re.fullmatch(r"([A-Za-z])_?(\d+)?", name).groups()
    return f"{letter}_{digits}" if digits else letter


def _parse_side(side: str) -> tuple["OrderedDict[str, Fraction]", Fraction]:
    """Parse one side of an (in)equality into variable coefficients and a constant."""
    coeffs: "OrderedDict[str, Fraction]" = OrderedDict()
    constant = Fraction(0)

    normalized = re.sub(r"\s+", "", side)
    if not normalized:
        return coeffs, constant
    if normalized[0] not in "+-":
        normalized = "+" + normalized

    for raw_term in re.findall(r"[+-][^+-]*", normalized):
        match = _TERM.match(raw_term)
        if match is None:
            raise ValueError(f"Cannot parse term {raw_term!r} in {side!r}")
        sign, number, variable = match.groups()
        magnitude = Fraction(number) if number else Fraction(1)
        value = -magnitude if sign == "-" else magnitude
        if variable:
            name = canonical_var(variable)
            coeffs[name] = coeffs.get(name, Fraction(0)) + value
        else:
            constant += value
    return coeffs, constant


def parse_linear_expression(expression: str) -> "OrderedDict[str, Fraction]":
    """Parse an expression (no relation sign) into ordered variable coefficients."""
    coeffs, _ = _parse_side(expression)
    return coeffs


def _parse_constraint(expression: str):
    """Split a constraint, normalise vars to the left and the constant to the right."""
    parts = _RELATION.split(expression, maxsplit=1)
    if len(parts) != 3:
        raise ValueError(f"Constraint {expression!r} has no <=, >= or = relation")
    lhs_str, sense, rhs_str = parts

    lhs_coeffs, lhs_const = _parse_side(lhs_str)
    rhs_coeffs, rhs_const = _parse_side(rhs_str)

    coeffs: "OrderedDict[str, Fraction]" = OrderedDict()
    for name, value in lhs_coeffs.items():
        coeffs[name] = coeffs.get(name, Fraction(0)) + value
    for name, value in rhs_coeffs.items():
        coeffs[name] = coeffs.get(name, Fraction(0)) - value
    rhs = rhs_const - lhs_const
    return coeffs, sense, rhs


def _collect_variables(objective_coeffs, constraint_coeffs) -> list[str]:
    """Ordered, de-duplicated variable list: objective first, then constraints."""
    variables: "OrderedDict[str, None]" = OrderedDict()
    for name in objective_coeffs:
        variables.setdefault(name, None)
    for coeffs in constraint_coeffs:
        for name in coeffs:
            variables.setdefault(name, None)
    return list(variables)


@dataclass
class StandardForm:
    """Standard-form data shared by every solver backend.

    Attributes mirror the textbook notation: ``A`` is the constraint matrix
    (including slack/artificial columns), ``b`` the right-hand side, ``c1`` the
    phase-1 objective coefficients and ``c2`` the original (phase-2) objective
    coefficients. ``objective_coeffs`` is the raw (never sign-flipped) objective
    row used to (re)build the tableau objective row. ``coeff_matrix`` is the
    initial simplex tableau (objective row zeroed); solvers mutate a copy of it.
    """

    num_vars: int
    num_slack_vars: int
    num_artificial_vars: int
    objective_sense: str
    objective_expr: str
    variables: list[str]
    constraints: list[str]
    constraint_senses: list[str]
    A: np.ndarray
    b: np.ndarray
    c1: np.ndarray
    c2: np.ndarray
    objective_coeffs: list[Fraction]
    var_names: list[str]
    slack_rows: list[int]
    artificial_rows: list[int]
    coeff_matrix: list[list[Fraction]]

    @property
    def total_vars(self) -> int:
        return self.num_vars + self.num_slack_vars + self.num_artificial_vars


def _count_auxiliary_vars(senses, method) -> tuple[int, int]:
    """Count slack/artificial variables implied by the constraint senses."""
    num_slack = 0
    num_artificial = 0
    for sense in senses:
        if sense == "<=":
            num_slack += 1
        elif sense == ">=":
            num_slack += 1
            if method == "simplex":
                num_artificial += 1
        elif sense == "=":
            if method == "simplex":
                num_artificial += 1
    return num_slack, num_artificial


def _variable_names(variables, slack_rows, artificial_rows) -> list[str]:
    """Build display names: variables, then ``h_i`` slacks and ``a_i`` artificials."""
    return (
        list(variables)
        + [f"h_{row}" for row in slack_rows]
        + [f"a_{row}" for row in artificial_rows]
    )


def build_standard_form(constraints, objective_function, method="simplex"):
    """Parse a problem description into a :class:`StandardForm` instance.

    The number of variables is inferred from the objective and constraints; no
    ``num_vars`` argument is needed.
    """
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Method {method!r} is not supported")

    objective_sense, objective_expr = objective_function
    objective_coeffs_map = parse_linear_expression(objective_expr)

    parsed = [_parse_constraint(expr) for expr in constraints]
    constraint_coeffs = [coeffs for coeffs, _, _ in parsed]
    senses = [sense for _, sense, _ in parsed]
    rhs_values = [rhs for _, _, rhs in parsed]

    if method == "lemke" and "=" in senses:
        raise ValueError("Equality constraints are not supported by Lemke's method")

    constraint_vars = {name for coeffs in constraint_coeffs for name in coeffs}
    orphan_vars = [name for name in objective_coeffs_map if name not in constraint_vars]
    if orphan_vars:
        raise ValueError(
            f"Variable(s) {', '.join(orphan_vars)} appear in the objective but in "
            f"no constraint. Check for a typo (e.g. a variable named differently in "
            f"the constraints) or an unbounded direction."
        )

    variables = _collect_variables(objective_coeffs_map, constraint_coeffs)
    var_index = {name: i for i, name in enumerate(variables)}
    num_vars = len(variables)

    num_slack, num_artificial = _count_auxiliary_vars(senses, method)
    total_vars = num_vars + num_slack + num_artificial

    coeff_matrix = [
        [Fraction(0) for _ in range(total_vars + 1)]
        for _ in range(len(constraints) + 1)
    ]

    slack_index = num_vars
    artificial_index = num_vars + num_slack
    slack_rows: list[int] = []
    artificial_rows: list[int] = []

    for i, (coeffs, sense, rhs) in enumerate(parsed, start=1):
        for name, value in coeffs.items():
            coeff_matrix[i][var_index[name]] = value
        if sense == "<=":
            coeff_matrix[i][slack_index] = Fraction(1)
            slack_index += 1
            slack_rows.append(i)
        elif sense == ">=":
            coeff_matrix[i][slack_index] = Fraction(-1)
            slack_index += 1
            slack_rows.append(i)
            if method == "simplex":
                coeff_matrix[i][artificial_index] = Fraction(1)
                artificial_index += 1
                artificial_rows.append(i)
        elif sense == "=":
            coeff_matrix[i][artificial_index] = Fraction(1)
            artificial_index += 1
            artificial_rows.append(i)
        coeff_matrix[i][-1] = rhs

    # Phase-1 objective: 0 for structural/slack vars, -1 for each artificial.
    c1 = [Fraction(0)] * (num_vars + num_slack) + [Fraction(-1)] * num_artificial

    # Phase-2 (original) objective placed across the full variable width.
    objective_coeffs = [Fraction(0)] * total_vars
    for name, value in objective_coeffs_map.items():
        objective_coeffs[var_index[name]] = value

    c1 = array_to_fraction(np.array(c1).reshape(-1, 1))
    c2 = array_to_fraction(np.array(objective_coeffs).reshape(-1, 1))
    if method == "lemke" and "min" in objective_sense:
        c2 = -c2

    A = array_to_fraction(np.array([row[:-1] for row in coeff_matrix[1:]]))
    b = array_to_fraction(np.array([row[-1] for row in coeff_matrix[1:]]).reshape(-1, 1))

    var_names = _variable_names(variables, slack_rows, artificial_rows)

    return StandardForm(
        num_vars=num_vars,
        num_slack_vars=num_slack,
        num_artificial_vars=num_artificial,
        objective_sense=objective_sense,
        objective_expr=objective_expr,
        variables=variables,
        constraints=list(constraints),
        constraint_senses=senses,
        A=A,
        b=b,
        c1=c1,
        c2=c2,
        objective_coeffs=objective_coeffs,
        var_names=var_names,
        slack_rows=slack_rows,
        artificial_rows=artificial_rows,
        coeff_matrix=coeff_matrix,
    )
