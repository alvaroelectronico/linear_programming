# -*- coding: utf-8 -*-
"""Dos fases (A): equality + <= rows, solved with the two-phase method.
Mirrors examples/dos_fases_a_sol.tex (the library's golden reference)."""

from linprog import latex, parse_problem, two_phase

from . import join_blocks

problem = parse_problem(
    """
    max x_1 + 4x_2
    4x_1 + 2x_2 = 80
    2x_1 + 3x_2 <= 60
    """
)


def statement() -> str:
    return join_blocks(
        r"Dado el siguiente problema, $P$, de programación lineal:",
        latex.problem_tex(problem),
        r"Se pide:",
        "\n".join([
            r"\begin{enumerate}",
            r"    \item \textbf{Formular} el problema correspondiente a la primera fase"
            r" (método de las dos fases).",
            r"    \item \textbf{Resolver} el problema $P$ mediante el método de la matriz"
            r" completa aplicando el método de las dos fases.",
            r"\end{enumerate}",
        ]),
    )


def solution() -> str:
    sf = problem.standard()
    sol = two_phase(sf)
    best = sol.final
    values = ", ".join(
        f"${name} = {latex.fmt(value)}$" for name, value in sol.values.items()
    )
    return join_blocks(
        latex.HDR_PHASE1,
        latex.phase1_tex(sf),
        latex.HDR_TWO_PHASE,
        latex.tableau(sol.bases, two_phase_split=sol.phase1_end, frac=True),
        latex.HDR_OPTIMAL_BASIS,
        latex.basis_matrix_tex(best),
        latex.basis_inverse_tex(best, frac=True),
        latex.HDR_MULTIPLIERS,
        latex.shadow_prices_tex(best, verbose=True, frac=True),
        latex.reduced_costs_tex(best, verbose=True, frac=True),
        latex.HDR_OBJECTIVE_VALUE,
        latex.objective_value_tex(best),
        rf"{latex.LBL_OPTIMAL_SOLUTION} {values}.",
        sol.message,
    )
