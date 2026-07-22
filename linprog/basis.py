"""Analysis of any basis of a standard-form problem.

A basis is just a tuple of column indices into ``StandardForm.variables``.
Every derived quantity (B, B^{-1}, shadow prices, reduced costs, ...) is a
cached property computed on first access, with exact Fraction arithmetic.

The module starts with the minimal exact linear algebra it needs — plain
lists of lists, no numpy.
"""

from __future__ import annotations

from fractions import Fraction
from functools import cached_property
from typing import Sequence

from .problem import StandardForm

Matrix = list[list[Fraction]]
Vector = list[Fraction]


class SingularBasisError(ValueError):
    """Raised when the chosen columns do not form an invertible basis."""


def dot(u: Sequence[Fraction], v: Sequence[Fraction]) -> Fraction:
    return sum((x * y for x, y in zip(u, v, strict=True)), Fraction(0))


def mat_vec(matrix: Matrix, v: Sequence[Fraction]) -> Vector:
    return [dot(row, v) for row in matrix]


def vec_mat(v: Sequence[Fraction], matrix: Matrix) -> Vector:
    return [dot(v, [row[j] for row in matrix]) for j in range(len(matrix[0]))]


def mat_mul(a: Matrix, b: Matrix) -> Matrix:
    cols = list(zip(*b))
    return [[dot(row, col) for col in cols] for row in a]


def identity(n: int) -> Matrix:
    return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]


def inverse(matrix: Matrix) -> Matrix:
    """Exact inverse by Gauss-Jordan elimination (row pivoting on the first
    nonzero entry — with Fractions there is no numerical-stability concern)."""
    n = len(matrix)
    aug = [list(row) + ident_row for row, ident_row in zip(matrix, identity(n))]
    for col in range(n):
        pivot_row = next((r for r in range(col, n) if aug[r][col] != 0), None)
        if pivot_row is None:
            raise SingularBasisError("The basis matrix is singular")
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]
        for r in range(n):
            if r != col and aug[r][col] != 0:
                factor = aug[r][col]
                aug[r] = [x - factor * y for x, y in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


class Basis:
    """One basis of a standard-form problem, identified by its column indices."""

    def __init__(self, sf: StandardForm, indices: Sequence[int]):
        if len(indices) != sf.n_rows:
            raise ValueError(
                f"A basis needs {sf.n_rows} columns, got {len(indices)}"
            )
        self.sf = sf
        self.indices: tuple[int, ...] = tuple(indices)

    def __repr__(self) -> str:
        return f"Basis({', '.join(self.names)})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Basis)
            and self.sf is other.sf
            and self.indices == other.indices
        )

    def __hash__(self) -> int:
        return hash((id(self.sf), self.indices))

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self.sf.variables[j] for j in self.indices)

    # --- exact linear algebra, all lazy -----------------------------------

    @cached_property
    def B(self) -> Matrix:
        return [[row[j] for j in self.indices] for row in self.sf.A]

    @cached_property
    def B_inv(self) -> Matrix:
        return inverse(self.B)

    @cached_property
    def c_B(self) -> Vector:
        return [self.sf.c[j] for j in self.indices]

    @cached_property
    def u(self) -> Vector:
        """Values of the basic variables: u^B = B^{-1} b."""
        return mat_vec(self.B_inv, self.sf.b)

    @cached_property
    def pi(self) -> Vector:
        """Simplex multipliers / shadow prices: pi^B = c^B B^{-1}."""
        return vec_mat(self.c_B, self.B_inv)

    @cached_property
    def B_inv_A(self) -> Matrix:
        """The tableau body: B^{-1} A (substitution rates)."""
        return mat_mul(self.B_inv, self.sf.A)

    @cached_property
    def V(self) -> Vector:
        """Reduced costs (simplex criterion): V^B = c - c^B B^{-1} A."""
        return self.reduced_costs(self.sf.c)

    @cached_property
    def z(self) -> Fraction:
        """Objective value (max form): z^B = c^B u^B."""
        return dot(self.c_B, self.u)

    def reduced_costs(self, c: Sequence[Fraction]) -> Vector:
        """Reduced costs for an arbitrary cost vector (e.g. the phase-1 one)."""
        c_basic = [c[j] for j in self.indices]
        pi = vec_mat(c_basic, self.B_inv)
        columns = list(zip(*self.sf.A))
        return [c[j] - dot(pi, columns[j]) for j in range(self.sf.n_cols)]

    def objective_value(self, c: Sequence[Fraction]) -> Fraction:
        """Objective value for an arbitrary cost vector."""
        return dot([c[j] for j in self.indices], self.u)

    def values(self) -> dict[str, Fraction]:
        """The full basic solution: every variable, non-basic ones at 0."""
        result = {name: Fraction(0) for name in self.sf.variables}
        for name, value in zip(self.names, self.u):
            result[name] = value
        return result

    # --- classification ----------------------------------------------------

    @property
    def _real_cols(self) -> range:
        """Columns that are not artificial variables."""
        return range(self.sf.n_cols - self.sf.n_artificials)

    @cached_property
    def is_feasible(self) -> bool:
        return all(value >= 0 for value in self.u)

    @cached_property
    def is_degenerate(self) -> bool:
        return any(value == 0 for value in self.u)

    @cached_property
    def is_optimal(self) -> bool:
        """Feasible and V^B <= 0 over the real (non-artificial) variables."""
        return self.is_feasible and all(self.V[j] <= 0 for j in self._real_cols)

    @cached_property
    def has_alternate_optimum(self) -> bool:
        """Optimal, with a zero reduced cost on some non-basic real variable."""
        return self.is_optimal and any(
            self.V[j] == 0 for j in self._real_cols if j not in self.indices
        )
