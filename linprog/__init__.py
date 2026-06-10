"""linprog: an educational linear-programming toolkit.

Parses linear programs from human-readable strings, solves them with the
two-phase Simplex method or Lemke's method using exact rational arithmetic
(:class:`fractions.Fraction`), and renders the intermediate work as LaTeX
tableaux for teaching material. An optional Gurobi backend is available for
cross-checking and sensitivity analysis.
"""

from linprog.problem import LinearProgram

__all__ = ["LinearProgram"]
