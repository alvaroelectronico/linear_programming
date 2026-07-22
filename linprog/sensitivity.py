"""Sensitivity analysis for a RHS term b_i and a cost term c_j, with the
worked derivation as LaTeX.

No symbolic-math dependency: every perturbed quantity is *affine* in the
parameter, so each component is just a ``(constant, coefficient)`` pair and
the validity interval falls out of linear inequalities.

- RHS: component k of ``u^B(b_i) = B^{-1} b`` is
  ``sum_{l != i} Binv[k][l] b_l  +  Binv[k][i] * b_i``; feasibility asks every
  component ``>= 0``.
- Cost of a *basic* variable ``x_j`` (position k in the basis): for each
  non-basic real column q, ``V_q(t) = V_q - (t - c_j) * p_kq`` with
  ``p_kq = (B^{-1}A)[k][q]``; optimality asks every ``V_q(t) <= 0``.
- Cost of a *non-basic* variable: only its own reduced cost moves,
  ``V_j(t) = t - pi . A_j <= 0``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import lcm

from .basis import Basis
from .latex import _equation, fmt, pmatrix

Affine = tuple[Fraction, Fraction]  # (constant, coefficient of the parameter)


@dataclass(frozen=True)
class Interval:
    """A closed interval; ``None`` means unbounded on that side."""

    lower: Fraction | None
    upper: Fraction | None

    def __contains__(self, value) -> bool:
        return (self.lower is None or value >= self.lower) and (
            self.upper is None or value <= self.upper
        )


def _interval(lowers: list[Fraction], uppers: list[Fraction]) -> Interval:
    return Interval(
        lower=max(lowers) if lowers else None,
        upper=min(uppers) if uppers else None,
    )


# --- b_i ----------------------------------------------------------------------


def _rhs_affines(basis: Basis, i: int) -> list[Affine]:
    """Components of u^B as affine functions of b_i."""
    b = basis.sf.b
    return [
        (
            sum((row[l] * b[l] for l in range(len(b)) if l != i), Fraction(0)),
            row[i],
        )
        for row in basis.B_inv
    ]


def rhs_range(basis: Basis, i: int) -> Interval:
    """Range of b_i (0-based constraint row) keeping the basis feasible."""
    lowers, uppers = [], []
    for const, coef in _rhs_affines(basis, i):
        if coef > 0:
            lowers.append(-const / coef)
        elif coef < 0:
            uppers.append(-const / coef)
    return _interval(lowers, uppers)


# --- c_j ----------------------------------------------------------------------


def _real_nonbasic(basis: Basis) -> list[int]:
    sf = basis.sf
    return [
        q for q in range(sf.n_cols - sf.n_artificials) if q not in basis.indices
    ]


def _cost_affines(basis: Basis, j: int) -> list[Affine]:
    """Non-basic reduced costs as affine functions of c_j (j basic)."""
    k = basis.indices.index(j)
    cj = basis.sf.c[j]
    return [
        (basis.V[q] + cj * basis.B_inv_A[k][q], -basis.B_inv_A[k][q])
        for q in _real_nonbasic(basis)
    ]


def cost_range(basis: Basis, j: int) -> Interval:
    """Range of c_j (0-based column) keeping the basis optimal.

    Works in max form (a min problem's coefficient arrives negated, like
    everything else downstream of ``standard()``).
    """
    sf = basis.sf
    if j >= sf.n_cols - sf.n_artificials:
        raise ValueError("Artificial variables have no cost range")
    if j not in basis.indices:
        # only V_j(t) = t - pi . A_j moves
        return Interval(lower=None, upper=sf.c[j] - basis.V[j])
    lowers, uppers = [], []
    for const, coef in _cost_affines(basis, j):
        # const + coef * t <= 0
        if coef > 0:
            uppers.append(-const / coef)
        elif coef < 0:
            lowers.append(-const / coef)
    return _interval(lowers, uppers)


# --- LaTeX --------------------------------------------------------------------


def affine_tex(affine: Affine, param: str, *, frac: bool = False) -> str:
    """``(40, -3/2)`` with param ``b_3`` renders as ``\\frac{80 - 3b_3}{2}``
    (or ``(80 - 3b_3)/2`` inline) — integers stay plain: ``180 - 8b_3``."""
    const, coef = affine
    if coef == 0:
        return fmt(const, frac=frac)
    denominator = lcm(const.denominator, coef.denominator)
    n0, n1 = int(const * denominator), int(coef * denominator)
    coef_part = f"{'' if abs(n1) == 1 else abs(n1)}{param}"
    if n0 == 0:
        numerator = f"-{coef_part}" if n1 < 0 else coef_part
    else:
        numerator = f"{n0} {'-' if n1 < 0 else '+'} {coef_part}"
    if denominator == 1:
        return numerator
    if frac:
        return rf"\frac{{{numerator}}}{{{denominator}}}"
    return f"({numerator})/{denominator}"


def interval_tex(interval: Interval, param: str, *, frac: bool = False) -> str:
    if interval.lower is not None and interval.upper is not None:
        return (
            f"{fmt(interval.lower, frac=frac)} \\leq {param}"
            f" \\leq {fmt(interval.upper, frac=frac)}"
        )
    if interval.lower is not None:
        return f"{param} \\geq {fmt(interval.lower, frac=frac)}"
    if interval.upper is not None:
        return f"{param} \\leq {fmt(interval.upper, frac=frac)}"
    return rf"-\infty < {param} < \infty"


def rhs_range_tex(basis: Basis, i: int, *, frac: bool = False) -> str:
    """The worked b_i derivation, as in examples/empresa_minera_a_sol.tex:
    ``u^B = B^{-1}b = (B^{-1})(b with symbolic b_i) >= 0 => (...) >= 0 =>
    interval``."""
    param = f"b_{i + 1}"
    symbolic_b = [
        [param if l == i else fmt(value, frac=frac)]
        for l, value in enumerate(basis.sf.b)
    ]
    components = [
        [affine_tex(affine, param, frac=frac)] for affine in _rhs_affines(basis, i)
    ]
    chain = (
        f"u^B = B^{{-1}}b = \n"
        f"{pmatrix(basis.B_inv, frac=frac)}\n"
        f"{pmatrix(symbolic_b, frac=frac)}\n"
        f"\\geq 0 \\Rightarrow\n"
        f"{pmatrix(components, frac=frac)}\n"
        f"\\geq 0 \\Rightarrow\n"
        f"{interval_tex(rhs_range(basis, i), param, frac=frac)}"
    )
    return _equation([chain])


def cost_range_tex(basis: Basis, j: int, *, frac: bool = False) -> str:
    """The worked c_j derivation: one optimality condition per non-basic
    variable, then the interval."""
    sf = basis.sf
    name = sf.variables[j]
    param = f"c_{{{name}}}"
    interval = cost_range(basis, j)  # also validates j
    if j not in basis.indices:
        bound = sf.c[j] - basis.V[j]  # pi . A_j
        lines = [
            f"V^B_{{{name}}} = {param} - \\pi^B A_{{{name}}}"
            f" = {param} - {fmt(bound, frac=frac)} \\leq 0",
            f"\\Rightarrow {interval_tex(interval, param, frac=frac)}",
        ]
        return _equation(lines)
    lines = [
        f"V^B_{{{sf.variables[q]}}} = {affine_tex(affine, param, frac=frac)} \\leq 0"
        for q, affine in zip(_real_nonbasic(basis), _cost_affines(basis, j))
    ]
    lines.append(f"\\Rightarrow {interval_tex(interval, param, frac=frac)}")
    return _equation(lines)
