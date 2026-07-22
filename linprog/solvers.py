"""Solvers: primal simplex (this phase), two-phase and dual simplex (later).

Each iteration builds a fresh, immutable ``Basis`` (revised-simplex style)
instead of mutating a tableau: the solver logic reduces to choosing the
entering and leaving variables, and the returned list of bases is directly
what the tableau renderer consumes.  Exam-sized problems make the extra
O(m^3) per iteration irrelevant.

Course conventions (max form): a basis is optimal when every real variable
has ``V_j <= 0``; the entering variable is the most positive ``V_j`` (ties:
lowest column index); the leaving row is the minimum ratio ``u_i / d_i`` over
``d_i > 0`` (ties: lowest row index).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from fractions import Fraction
from typing import Sequence

from .basis import Basis
from .problem import StandardForm

# Spanish wording used in the exams for the terminal states.
MSG_UNBOUNDED = (
    "El problema no está acotado y, por lo tanto, no tiene solución óptima."
)
MSG_INFEASIBLE = (
    "El problema no tiene solución factible y, por lo tanto, no tiene solución óptima."
)

_MAX_ITERATIONS = 1000


class Status(Enum):
    OPTIMAL = auto()
    UNBOUNDED = auto()
    INFEASIBLE = auto()


@dataclass
class Solution:
    """Result of a solver run: the status plus every basis visited, in order."""

    status: Status
    bases: list[Basis]
    phase1_end: int | None = None  # two-phase: bases[:phase1_end] are phase 1

    @property
    def final(self) -> Basis:
        return self.bases[-1]

    @property
    def z(self) -> Fraction:
        """Objective value of the last basis, in max form (as in the tableau)."""
        return self.final.z

    @property
    def objective_value(self) -> Fraction:
        """Objective value of the original problem (negated back for min)."""
        sign = 1 if self.final.sf.problem.goal == "max" else -1
        return sign * self.z

    @property
    def values(self) -> dict[str, Fraction]:
        """Optimal values of the decision variables only."""
        all_values = self.final.values()
        return {name: all_values[name] for name in self.final.sf.problem.variables}

    @property
    def degenerate(self) -> bool:
        return any(basis.is_degenerate for basis in self.bases)

    @property
    def alternate_optima(self) -> bool:
        return self.status is Status.OPTIMAL and self.final.has_alternate_optimum

    @property
    def message(self) -> str:
        if self.status is Status.UNBOUNDED:
            return MSG_UNBOUNDED
        if self.status is Status.INFEASIBLE:
            return MSG_INFEASIBLE
        return ""


def _pivot(basis: Basis, entering: int) -> list[int] | None:
    """Choose the leaving row for ``entering`` by the minimum-ratio test.
    Returns the new basis indices, or None if no ratio exists (unbounded ray)."""
    direction = [row[entering] for row in basis.B_inv_A]
    best_row, best_ratio = None, None
    for i, d in enumerate(direction):
        if d <= 0:
            continue
        ratio = basis.u[i] / d
        if best_ratio is None or ratio < best_ratio:
            best_row, best_ratio = i, ratio
    if best_row is None:
        return None
    indices = list(basis.indices)
    indices[best_row] = entering
    return indices


def _entering_column(
    basis: Basis, c: Sequence[Fraction], allowed_cols: Sequence[int]
) -> int | None:
    """Most positive reduced cost among the allowed non-basic columns."""
    reduced = basis.reduced_costs(c)
    best, best_value = None, Fraction(0)
    for j in allowed_cols:
        if j in basis.indices:
            continue
        if reduced[j] > best_value:
            best, best_value = j, reduced[j]
    return best


def _primal(
    sf: StandardForm,
    start: Sequence[int],
    c: Sequence[Fraction],
    allowed_cols: Sequence[int],
) -> tuple[Status, list[Basis]]:
    """Primal simplex engine over an arbitrary cost vector.  Assumes the
    starting basis is feasible."""
    basis = Basis(sf, start)
    bases = [basis]
    for _ in range(_MAX_ITERATIONS):
        entering = _entering_column(basis, c, allowed_cols)
        if entering is None:
            return Status.OPTIMAL, bases
        indices = _pivot(basis, entering)
        if indices is None:
            return Status.UNBOUNDED, bases
        basis = Basis(sf, indices)
        bases.append(basis)
    raise RuntimeError("Simplex did not converge (cycling?)")


def two_phase(sf: StandardForm) -> Solution:
    """Two-phase simplex.

    Phase 1 maximises ``z' = -sum(artificials)`` from the identity basis; if
    its optimum is negative the problem is infeasible.  Basic artificials
    stuck at zero are driven out before phase 2 re-optimises the original
    objective.  ``Solution.phase1_end`` is the number of leading bases that
    belong to phase 1 — pass it to ``latex.tableau(two_phase_split=...)`` so
    those blocks carry both objective rows.

    Problems with no artificial variables fall back to a plain simplex run.
    """
    if not sf.needs_two_phase():
        return simplex(sf)

    real_cols = range(sf.n_cols - sf.n_artificials)
    c1 = sf.phase1_c()
    status1, bases = _primal(sf, sf.initial_basis(), c1, real_cols)
    assert status1 is Status.OPTIMAL  # z' <= 0, phase 1 cannot be unbounded

    if bases[-1].objective_value(c1) < 0:
        return Solution(Status.INFEASIBLE, bases, phase1_end=len(bases))

    # Drive out any artificial still basic at level 0 (degenerate phase-1
    # optimum): pivot it for a real non-basic column with a nonzero entry in
    # its row.  An all-zero row means a redundant constraint — the artificial
    # then stays basic at 0 and is simply never allowed to enter again.
    basis = bases[-1]
    n_real = sf.n_cols - sf.n_artificials
    for row, col in enumerate(basis.indices):
        if col >= n_real and basis.u[row] == 0:
            entering = next(
                (j for j in real_cols
                 if j not in basis.indices and basis.B_inv_A[row][j] != 0),
                None,
            )
            if entering is not None:
                indices = list(basis.indices)
                indices[row] = entering
                basis = Basis(sf, indices)
                bases.append(basis)
    phase1_end = len(bases)

    status2, bases2 = _primal(sf, basis.indices, sf.c, real_cols)
    bases += bases2[1:]  # bases2[0] is the phase-1 final basis again
    return Solution(status=status2, bases=bases, phase1_end=phase1_end)


def dual_simplex(sf: StandardForm, start: Sequence[int] | None = None) -> Solution:
    """Dual simplex (Lemke's method, as taught in the course).

    Starts from a basis satisfying the optimality criterion (``V_j <= 0`` for
    every real variable) but possibly infeasible (some ``u_i < 0``) — by
    default the all-slacks basis, which requires a problem without ``=`` rows
    (use ``Problem.split_equalities()`` first).  Each iteration the most
    negative ``u_i`` picks the leaving row, and the entering column minimises
    ``V_j / d_j`` over the row's negative entries ``d_j``.  A negative row
    with no negative entry proves infeasibility.

    Artificial columns (present when the problem has ``>=`` rows) take no part
    in the method; render the tableau with ``include_artificials=False``.
    """
    if start is None:
        start = sf.slack_basis()
    real_cols = range(sf.n_cols - sf.n_artificials)

    basis = Basis(sf, start)
    not_optimal = [sf.variables[j] for j in real_cols if basis.V[j] > 0]
    if not_optimal:
        raise ValueError(
            "The dual simplex needs a starting basis satisfying V <= 0; "
            f"positive reduced costs on: {', '.join(not_optimal)}"
        )

    bases = [basis]
    for _ in range(_MAX_ITERATIONS):
        if basis.is_feasible:
            return Solution(status=Status.OPTIMAL, bases=bases)
        leaving_row = min(range(sf.n_rows), key=lambda i: (basis.u[i], i))
        row = basis.B_inv_A[leaving_row]
        candidates = [
            (basis.V[j] / row[j], j)
            for j in real_cols
            if j not in basis.indices and row[j] < 0
        ]
        if not candidates:
            return Solution(status=Status.INFEASIBLE, bases=bases)
        _, entering = min(candidates)
        indices = list(basis.indices)
        indices[leaving_row] = entering
        basis = Basis(sf, indices)
        bases.append(basis)
    raise RuntimeError("Dual simplex did not converge (cycling?)")


def simplex(sf: StandardForm, start: Sequence[int] | None = None) -> Solution:
    """Primal simplex from a feasible basis.

    Without ``start``, the all-slacks identity basis is used, which requires a
    problem with no artificial variables (all ``<=`` rows); otherwise solve
    with ``two_phase`` or provide a feasible ``start`` explicitly.
    """
    if start is None:
        if sf.needs_two_phase():
            raise ValueError(
                "No feasible identity basis (the problem has '=' or '>=' rows): "
                "use two_phase(sf) or pass a feasible start basis."
            )
        start = sf.initial_basis()
    if not Basis(sf, start).is_feasible:
        raise ValueError(f"The starting basis {list(start)} is not feasible")

    real_cols = range(sf.n_cols - sf.n_artificials)
    status, bases = _primal(sf, start, sf.c, real_cols)
    return Solution(status=status, bases=bases)
