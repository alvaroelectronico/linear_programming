"""Sandbox: try out the linprog library as it grows.

Run with:  python sandbox.py

This file is a playground, not part of the library. Each section shows how to
use what is implemented so far; new sections will be added as new phases land.
"""

from linprog import parse_problem

# # ---------------------------------------------------------------------------
# # Phase 1 — parsing a problem from plain text
# # ---------------------------------------------------------------------------

# # The parser is forgiving: spaces are optional, x1 == x_1, coefficients may be
# # implicit (x), decimal (2.5x) or fractions (3/2y), and variables/constants may
# # appear on either side of a constraint.
# problem = parse_problem(
#     """
#     max 3x1 + 4x2
#     x1+2x2<=50
#     x1+x2>=10
#     """
# )

# print("goal:         ", problem.goal)
# print("objective:    ", problem.objective)
# print("variables:    ", problem.variables)
# print("n_vars:       ", problem.n_vars)
# print("n_constraints:", problem.n_constraints)
# print("A:            ", problem.A)
# print("b:            ", problem.b)
# print("c:            ", problem.c)
# print("senses:       ", problem.senses)

# # Every number is an exact fractions.Fraction — no floats anywhere:
# first = problem.constraints[0]
# print("first constraint:", first.coeffs, first.sense, first.rhs)

# # A min problem with fractional/decimal coefficients:
# diet = parse_problem(
#     """
#     min 2.5x + 3/2y
#     x + y >= 10
#     2x + y >= 12
#     """
# )
# print()
# print("diet goal:     ", diet.goal)
# print("diet objective:", diet.objective)  # {'x': 5/2, 'y': 3/2}

# # ---------------------------------------------------------------------------
# # Phase 2 — standard form and LaTeX formulations
# # ---------------------------------------------------------------------------
# from linprog import latex

# exam = parse_problem(
#     """
#     max 3x_1 + 2x_2 + x_3
#     2x_1 + 4x_2 + 2x_3 >= 80
#     4x_1 + 3x_2 = 60
#     x_1 + x_2 + x_3 <= 15
#     """
# )

# # The standard form: slacks h_i (by constraint row), artificials a_k for the
# # two-phase method, min converted to max, b >= 0. Everything derived, exact.
# sf = exam.standard()
# print()
# print("columns:      ", sf.variables)   # x's, then h_1/h_3, then a_1/a_2
# print("A row 1:      ", sf.A[0])
# print("initial basis:", [sf.variables[j] for j in sf.initial_basis()])

# # LaTeX fragments (Spanish exam material). frac=True switches a/b -> \frac{a}{b}.
# print()
# print("--- original formulation ---")
# print(latex.problem_tex(exam))
# print("--- standard form ---")
# print(latex.standard_form_tex(sf))
# print("--- phase 1 formulation ---")
# print(latex.HDR_PHASE1)
# print(latex.phase1_tex(sf))
# print("--- canonical form ---")
# print(latex.canonical_form_tex(exam))
# print("--- elements ---")
# elements = latex.elements_tex(exam)
# print("A =", elements["A"])
# print("b =", elements["b"])
# print("c =", elements["c"])

# # ---------------------------------------------------------------------------
# # Phase 3 — analysing any basis: B, B^-1, u, pi (shadow prices), V, z
# # ---------------------------------------------------------------------------
# from linprog import Basis

# # The dos_fases_a exam problem; its optimal basis is (x_1, x_2).
# dos_fases = parse_problem(
#     """
#     max x_1 + 4x_2
#     4x_1 + 2x_2 = 80
#     2x_1 + 3x_2 <= 60
#     """
# )
# sf2 = dos_fases.standard()          # columns: x_1, x_2, h_2, a_1

# # A basis is just the list of column indices — ANY basis, not only the ones a
# # solver visits. Everything below is computed lazily and exactly.
# opt = Basis(sf2, [0, 1])            # (x_1, x_2)
# print()
# print("basis:        ", opt.names)
# print("B:            ", opt.B)       # [[4, 2], [2, 3]]
# print("B^-1:         ", opt.B_inv)   # [[3/8, -1/4], [-1/4, 1/2]]
# print("u = B^-1 b:   ", opt.u)       # [15, 10]  (values of basic variables)
# print("pi (shadow):  ", opt.pi)      # [-5/8, 7/4]
# print("V (red. costs):", opt.V)      # [0, 0, -7/4, 5/8]
# print("z:            ", opt.z)       # 55
# print("solution:     ", opt.values())
# print("feasible/optimal/degenerate:", opt.is_feasible, opt.is_optimal, opt.is_degenerate)

# # And their LaTeX renderings (frac=True for \frac{a}{b}):
# print()
# print(latex.basis_matrix_tex(opt))
# print(latex.basis_inverse_tex(opt, frac=True))
# print(latex.shadow_prices_tex(opt))
# print(latex.reduced_costs_tex(opt))       # artificial columns hidden
# print(latex.objective_value_tex(opt))

# ---------------------------------------------------------------------------
# Phase 4 — primal simplex
# ---------------------------------------------------------------------------
from linprog import latex, simplex  # latex again: phases 1-3 are commented out

# All-<= problems start from the slack basis; the solver records every basis
# it visits (that list feeds the tableau renderer in phase 5).
production = parse_problem(
    """
    max 2x + 3y
    x + y <= 4
    x + 3y <= 6
    """
)
solution = simplex(production.standard())
print()
print("status:         ", solution.status.name)
print("visited bases:  ", [basis.names for basis in solution.bases])
print("solution:       ", solution.values)            # {'x': 3, 'y': 1}
print("z (max form):   ", solution.z)                 # 9
print("objective value:", solution.objective_value)   # 9 (negated back if min)
print("degenerate:     ", solution.degenerate)
print("alternate optima:", solution.alternate_optima)

# The problem's elements (phase 2 API) work here too:
production_elements = latex.elements_tex(production)
print()
print("--- elements of the production problem ---")
print()
print("A =", production_elements["A"])
print()
print("b =", production_elements["b"])
print()
print("c =", production_elements["c"])

# Every basis the simplex visited, with its key numbers (phase 3 API — each
# Basis in solution.bases is a full Basis object):
print()
print("--- all visited bases ---")
for step, basis in enumerate(solution.bases):
    print(
        f"iter {step}: {basis.names}  u={basis.u}  z={basis.z}  "
        f"feasible={basis.is_feasible} optimal={basis.is_optimal}"
    )

# ...and, for one of them (the optimal one), every element in detail:
best = solution.final
print()
print("--- optimal basis in detail ---")
print("names:        ", best.names)
print("B:            ", best.B)
print("B^-1:         ", best.B_inv)
print("c_B:          ", best.c_B)
print("u = B^-1 b:   ", best.u)
print("pi (shadow):  ", best.pi)
print("V (red. costs):", best.V)
print("B^-1 A:       ", best.B_inv_A)
print("z:            ", best.z)
print("values:       ", best.values())

print()
print("--- optimal basis as LaTeX ---")
print()
print(latex.basis_matrix_tex(best))
print()
print(latex.basis_inverse_tex(best))
print()
print(latex.objective_value_tex(best))

# Shadow prices and reduced costs support verbose=True: the generic formula
# plus the fully expanded matrix products, as in the worked solutions.
print()
print("--- shadow prices, verbose=False ---")
print()
print(latex.shadow_prices_tex(best))
print()
print("--- shadow prices, verbose=True ---")
print()
print(latex.shadow_prices_tex(best, verbose=True))
print()
print("--- reduced costs, verbose=False ---")
print()
print(latex.reduced_costs_tex(best))
print()
print("--- reduced costs, verbose=True ---")
print()
print(latex.reduced_costs_tex(best, verbose=True))

# ---------------------------------------------------------------------------
# Phase 5 — the simplex tableau (same production problem and solution)
# ---------------------------------------------------------------------------

# All the visited bases stacked in one tableau, in the exam format:
print()
print("--- full tableau (all visited bases) ---")
print()
print(latex.tableau(solution.bases))

# Any subset of bases works: e.g. only the optimal one, or only the first.
print()
print("--- tableau of the optimal basis only ---")
print()
print(latex.tableau([solution.final]))

# frac=True renders 2/3 as \frac{2}{3}:
print()
print("--- first iteration, frac=True ---")
print()
print(latex.tableau(solution.bases[:1], frac=True))

# Terminal states carry the exam wording in Spanish:
unbounded = simplex(parse_problem("max x\nx - y <= 1").standard())
print()
print("status: ", unbounded.status.name)
print("message:", unbounded.message)

# ---------------------------------------------------------------------------
# Phase 6 — two-phase method (problems with = or >= rows)
# ---------------------------------------------------------------------------
from linprog import two_phase

# The dos_fases_a exam problem: the '=' row needs an artificial, so the
# two-phase method applies. Same workflow as before: solve, then rescue.
dos_fases = parse_problem(
    """
    max x_1 + 4x_2
    4x_1 + 2x_2 = 80
    2x_1 + 3x_2 <= 60
    """
)
sf_df = dos_fases.standard()
sol_df = two_phase(sf_df)
print()
print("status:       ", sol_df.status.name)
print("visited bases:", [basis.names for basis in sol_df.bases])
print("phase1_end:   ", sol_df.phase1_end)   # bases before it are phase 1
print("solution:     ", sol_df.values)       # {'x_1': 15, 'x_2': 10}
print("z:            ", sol_df.z)            # 55

# The phase-1 formulation (phase 2 API) and the full stacked tableau: pass
# phase1_end so phase-1 blocks carry the two objective rows Fase 1 / Fase 2.
print()
print(latex.HDR_PHASE1)
print()
print(latex.phase1_tex(sf_df))
print()
print(latex.HDR_TWO_PHASE)
print()
print(latex.tableau(sol_df.bases, two_phase_split=sol_df.phase1_end, frac=True))

# include_artificials=False drops the artificial columns (row labels stay):
print()
print("--- same tableau without the artificial columns ---")
print()
print(
    latex.tableau(
        sol_df.bases,
        two_phase_split=sol_df.phase1_end,
        include_artificials=False,
        frac=True,
    )
)

# An infeasible problem reports itself after the tableau:
infeasible = two_phase(
    parse_problem(
        """
        max 3x_1 + 2x_2 + x_3
        2x_1 + 4x_2 + 2x_3 >= 80
        4x_1 + 3x_2 = 60
        x_1 + x_2 + x_3 <= 15
        """
    ).standard()
)
print()
print("status: ", infeasible.status.name)
print("message:", infeasible.message)

# ---------------------------------------------------------------------------
# Phase 7 — dual simplex (Lemke's method)
# ---------------------------------------------------------------------------
from linprog import dual_simplex

# The lemke_sol exam problem: a min problem with an '=' row. Lemke needs a
# slack per row, so first split the equality into <= / >=:
lemke = parse_problem(
    """
    min 10x_1 + 20x_2 + 30x_3
    4x_1 + 2x_2 + 8x_3 <= 1000
    x_2 + x_3 = 500
    """
)
lemke_split = lemke.split_equalities()
sf_lk = lemke_split.standard()

print()
print("--- equivalent problem for Lemke (equality split) ---")
print()
print(latex.standard_form_tex(sf_lk))

# The all-slacks basis satisfies V <= 0 (max form of a min problem) and is
# infeasible (h_3 = -500): exactly what the dual simplex wants.
sol_lk = dual_simplex(sf_lk)
print()
print("status:       ", sol_lk.status.name)
print("visited bases:", [basis.names for basis in sol_lk.bases])
print("solution:     ", sol_lk.values)            # {'x_2': 500, ...}
print("z (max form): ", sol_lk.z)                 # -10000
print("objective:    ", sol_lk.objective_value)   # 10000 (original min)
print("degenerate:   ", sol_lk.degenerate)        # True: h_1 = h_2 = 0

# The exam tableau: unlabeled objective rows, artificials hidden, and the
# value column headed $s$ as in the example:
print()
print("--- Lemke tableau ---")
print()
print(latex.tableau(sol_lk.bases, include_artificials=False, value_label="s"))

# ---------------------------------------------------------------------------
# Phase 9 — sensitivity analysis for b_i and c_j
# ---------------------------------------------------------------------------
from linprog import sensitivity

# The empresa_minera exam problem, at its optimal basis (x_4, x_2, x_3):
minera = parse_problem(
    """
    max 250x_1 + 300x_2 + 400x_3 + 100x_4
    5x_1 + 3x_2 + 5x_3 + x_4 <= 100
    x_1 + 5x_2 + 3x_3 = 80
    x_2 + x_3 >= 20
    """
)
sol_mn = two_phase(minera.standard())
best_mn = sol_mn.final
print()
print("optimal basis:", best_mn.names, " z =", best_mn.z)

# Range of b_3 (the >= 20 commitment) keeping the same basis feasible.
# Numeric result first, then the worked derivation as in the exam solutions:
interval_b3 = sensitivity.rhs_range(best_mn, 2)      # rows are 0-based
print()
print("b_3 range:", interval_b3)                     # 16 <= b_3 <= 45/2
print()
print("--- worked b_3 derivation ---")
print()
print(sensitivity.rhs_range_tex(best_mn, 2, frac=True))

# Range of a cost coefficient: c of x_2 (basic) and c of x_1 (non-basic).
print()
print("c_{x_2} range:", sensitivity.cost_range(best_mn, 1))
print("c_{x_1} range:", sensitivity.cost_range(best_mn, 0))
print()
print("--- worked c_{x_2} derivation (basic variable) ---")
print()
print(sensitivity.cost_range_tex(best_mn, 1))
print()
print("--- worked c_{x_1} derivation (non-basic variable) ---")
print()
print(sensitivity.cost_range_tex(best_mn, 0))

