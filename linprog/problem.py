"""Core data model: Problem and Constraint.

A Problem stores exactly what the user wrote (goal, objective coefficients,
constraints); everything else (variable order, matrices, standard form) is
derived on demand.  All numbers are exact ``fractions.Fraction``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
from typing import Literal

Sense = Literal["<=", ">=", "="]
Goal = Literal["max", "min"]


@dataclass(frozen=True)
class Constraint:
    """A linear constraint ``sum(coeffs) sense rhs`` (variables on the left)."""

    coeffs: dict[str, Fraction]
    sense: Sense
    rhs: Fraction


@dataclass(frozen=True)
class Problem:
    """A linear program as written by the user (before any reformulation)."""

    goal: Goal
    objective: dict[str, Fraction]
    constraints: tuple[Constraint, ...]

    @cached_property
    def variables(self) -> list[str]:
        """Variable names ordered by first appearance (objective first)."""
        seen: dict[str, None] = {}
        for name in self.objective:
            seen.setdefault(name)
        for constraint in self.constraints:
            for name in constraint.coeffs:
                seen.setdefault(name)
        return list(seen)

    @property
    def n_vars(self) -> int:
        return len(self.variables)

    @property
    def n_constraints(self) -> int:
        return len(self.constraints)

    @property
    def A(self) -> list[list[Fraction]]:
        """Constraint coefficient matrix (m x n), following ``variables`` order."""
        zero = Fraction(0)
        return [
            [constraint.coeffs.get(name, zero) for name in self.variables]
            for constraint in self.constraints
        ]

    @property
    def b(self) -> list[Fraction]:
        """Right-hand sides."""
        return [constraint.rhs for constraint in self.constraints]

    @property
    def c(self) -> list[Fraction]:
        """Objective coefficients, following ``variables`` order."""
        zero = Fraction(0)
        return [self.objective.get(name, zero) for name in self.variables]

    @property
    def senses(self) -> list[Sense]:
        return [constraint.sense for constraint in self.constraints]

    def split_equalities(self) -> Problem:
        """An equivalent problem with every ``=`` constraint replaced by the
        pair ``<=`` / ``>=`` (in place, keeping the row order).  This is the
        reformulation the dual simplex (Lemke) needs, since it starts from the
        all-slacks basis and ``=`` rows carry no slack."""
        constraints: list[Constraint] = []
        for constraint in self.constraints:
            if constraint.sense == "=":
                constraints.append(Constraint(constraint.coeffs, "<=", constraint.rhs))
                constraints.append(Constraint(constraint.coeffs, ">=", constraint.rhs))
            else:
                constraints.append(constraint)
        return Problem(self.goal, self.objective, tuple(constraints))

    def standard(self) -> StandardForm:
        """Reformulate as a standard-form maximisation problem.

        - ``min`` objectives are negated (max form); the original is kept in
          ``StandardForm.problem`` for rendering.
        - Rows with a negative right-hand side are negated first (b >= 0).
        - Every inequality gets a slack ``h_i`` (+1 for ``<=``, -1 for ``>=``)
          named after its constraint row (1-based).
        - Rows without a +1 basic column (``=`` and ``>=`` rows) get an
          artificial ``a_i``, named after its constraint row like the slacks
          (see examples/empresa_minera_a_sol.tex: a_2, a_3 on rows 2 and 3).
          Artificials are extra columns used only by the two-phase method; the
          standard form itself is rendered without them.
        """
        zero, one = Fraction(0), Fraction(1)
        decision = self.variables

        rows: list[list[Fraction]] = []
        rhs: list[Fraction] = []
        senses: list[Sense] = []
        for constraint in self.constraints:
            coeffs = [constraint.coeffs.get(name, zero) for name in decision]
            sense, value = constraint.sense, constraint.rhs
            if value < 0:
                coeffs = [-x for x in coeffs]
                value = -value
                sense = {"<=": ">=", ">=": "<=", "=": "="}[sense]
            rows.append(coeffs)
            rhs.append(value)
            senses.append(sense)

        slack_vars: list[str] = []
        slack_signs: list[Fraction] = []
        slack_rows: list[int] = []
        artificial_vars: list[str] = []
        artificial_rows: list[int] = []
        for i, sense in enumerate(senses):
            if sense != "=":
                slack_vars.append(f"h_{i + 1}")
                slack_signs.append(one if sense == "<=" else -one)
                slack_rows.append(i)
            if sense != "<=":
                artificial_vars.append(f"a_{i + 1}")
                artificial_rows.append(i)

        variables = decision + slack_vars + artificial_vars
        A = [
            row
            + [slack_signs[k] if slack_rows[k] == i else zero for k in range(len(slack_vars))]
            + [one if artificial_rows[k] == i else zero for k in range(len(artificial_vars))]
            for i, row in enumerate(rows)
        ]
        sign = one if self.goal == "max" else -one
        c = [sign * x for x in self.c] + [zero] * (len(slack_vars) + len(artificial_vars))

        return StandardForm(
            problem=self,
            variables=variables,
            A=A,
            b=rhs,
            c=c,
            n_decision=len(decision),
            slack_vars=slack_vars,
            slack_rows=slack_rows,
            artificial_vars=artificial_vars,
            artificial_rows=artificial_rows,
        )


@dataclass(frozen=True)
class StandardForm:
    """Equality form ``A x = b`` (b >= 0) of a maximisation problem.

    Column order: decision variables, slacks ``h_i``, artificials ``a_k``.
    ``c`` is always the max-form objective (a ``min`` problem arrives negated).
    """

    problem: Problem
    variables: list[str]
    A: list[list[Fraction]]
    b: list[Fraction]
    c: list[Fraction]
    n_decision: int
    slack_vars: list[str]
    slack_rows: list[int]
    artificial_vars: list[str]
    artificial_rows: list[int]

    @property
    def n_rows(self) -> int:
        return len(self.b)

    @property
    def n_cols(self) -> int:
        return len(self.variables)

    @property
    def n_artificials(self) -> int:
        return len(self.artificial_vars)

    def needs_two_phase(self) -> bool:
        return bool(self.artificial_vars)

    def initial_basis(self) -> list[int]:
        """Identity starting basis: per row, its artificial if it has one,
        otherwise its (+1) slack."""
        n_slacks = len(self.slack_vars)
        basic_by_row: dict[int, int] = {
            row: self.n_decision + k for k, row in enumerate(self.slack_rows)
        }
        for k, row in enumerate(self.artificial_rows):
            basic_by_row[row] = self.n_decision + n_slacks + k
        return [basic_by_row[i] for i in range(self.n_rows)]

    def slack_basis(self) -> list[int]:
        """The all-slacks basis (dual simplex start).  Requires every row to
        have a slack, i.e. no ``=`` constraints."""
        if len(self.slack_vars) != self.n_rows:
            raise ValueError(
                "The slack basis requires a slack per row (no '=' constraints); "
                "split equalities into <= and >= first."
            )
        return [self.n_decision + k for k in range(len(self.slack_vars))]

    def phase1_c(self) -> list[Fraction]:
        """Phase-1 objective: max z' = -sum of artificials."""
        c = [Fraction(0)] * self.n_cols
        n_slacks = len(self.slack_vars)
        for k in range(len(self.artificial_vars)):
            c[self.n_decision + n_slacks + k] = Fraction(-1)
        return c
