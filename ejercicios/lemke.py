# -*- coding: utf-8 -*-
"""Lemke (dual simplex): a min problem with an '=' row that must be split
before the method applies. Mirrors examples/lemke_sol.tex."""

from linprog import dual_simplex, latex, parse_problem

from . import join_blocks

problem = parse_problem(
    """
    min 10x_1 + 20x_2 + 30x_3
    4x_1 + 2x_2 + 8x_3 <= 1000
    x_2 + x_3 = 500
    """
)


def statement() -> str:
    return join_blocks(
        r"Dado el siguiente problema de programación lineal:",
        latex.problem_tex(problem),
        r"Se pide:",
        "\n".join([
            r"\begin{enumerate}",
            r"    \item \textbf{Explicar} si cumple los requisitos para que se pueda"
            r" aplicar el método de Lemke y, si no es así, obtener un problema"
            r" equivalente que sí cumpla con dichos requisitos.",
            r"    \item \textbf{Obtener} la solución óptima del problema haciendo uso"
            r" del método de Lemke.",
            r"\end{enumerate}",
        ]),
    )


def solution() -> str:
    equivalent = problem.split_equalities()
    sf = equivalent.standard()
    sol = dual_simplex(sf)
    return join_blocks(
        r"Para aplicar el método de Lemke se necesita una solución básica que"
        r" cumpla el criterio de optimalidad, lo que exige un problema de máximos"
        r" sin restricciones de igualdad. Se desdobla la igualdad en dos"
        r" desigualdades y se reformula como maximización en forma estándar:",
        latex.standard_form_tex(sf),
        r"Las variables de holgura forman una base que cumple el criterio de"
        r" optimalidad (todos los costes reducidos son no positivos) aunque no es"
        r" factible ($h_3 < 0$), que es el punto de partida del método:",
        latex.tableau(sol.bases, include_artificials=False, value_label="s", frac=True),
        r"En la solución óptima del problema original:",
        "\n".join([
            r"\begin{itemize}",
            rf"    \item $z = -s = {latex.fmt(sol.objective_value)}$",
            *(
                rf"    \item ${name} = {latex.fmt(value)}$"
                for name, value in sol.values.items()
            ),
            r"\end{itemize}",
        ]),
        sol.message,
    )
