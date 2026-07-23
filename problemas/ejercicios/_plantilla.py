# -*- coding: utf-8 -*-
"""PLANTILLA de ejercicio. Copia este archivo a problemas/ejercicios/<id>.py
(el nombre del archivo es el id del ejercicio), edita el modelo, el enunciado
y la solución, y ejecuta `python -m problemas.ejercicios <id>` desde la raíz
del repo para generar:

    problemas/tex/<id>.tex        (enunciado,  desde statement())
    problemas/tex/<id>_sol.tex    (solución,   desde solution() — opcional)

que problemas/main.tex importa con \\input{tex/<id>} y \\input{tex/<id>_sol}.

La idea es intercalar texto en español con llamadas a linprog. API útil:

  Problema y formas (linprog.latex):
    problem_tex(p)            formulación original
    standard_form_tex(sf)     forma estándar (sin artificiales)
    canonical_form_tex(p)     forma canónica
    phase1_tex(sf)            formulación de la primera fase
    elements_tex(p)           {"A": ..., "b": ..., "c": ...} en pmatrix

  Resolución (linprog):
    simplex(sf) / two_phase(sf) / dual_simplex(sf)  -> Solution
    Solution: .status, .bases (todas las visitadas), .phase1_end,
              .values (dict de variables de decisión), .z, .objective_value,
              .degenerate, .alternate_optima, .message (texto en español)

  Tablas y elementos de una base (linprog.latex):
    tableau(bases, two_phase_split=, include_artificials=, frac=, value_label=)
    basis_matrix_tex(b) / basis_inverse_tex(b)
    shadow_prices_tex(b, verbose=) / reduced_costs_tex(b, verbose=)
    objective_value_tex(b)
    Encabezados listos: HDR_PHASE1, HDR_TWO_PHASE, HDR_OPTIMAL_BASIS,
                        HDR_MULTIPLIERS, HDR_OBJECTIVE_VALUE,
                        LBL_OPTIMAL_SOLUTION

  Sensibilidad (linprog.sensitivity):
    rhs_range(b, i) / rhs_range_tex(b, i)      intervalo de b_i (i por fila, 0-based)
    cost_range(b, j) / cost_range_tex(b, j)    intervalo de c_j (j por columna)

  Post-optimización (añadir restricciones a una base óptima):
    post = postoptimize(base_optima, "x_3 <= 8")   (o lista; '=' se desdobla)
    post.was_feasible / post.initial / post.solution (Solution normal)
    introduce_rows_tex(post, ...)   tabla de introducción de las filas nuevas
    tableau(post.solution.bases, ...)   tabla de la re-optimización (Lemke)

  Todas las funciones de render aceptan frac= (False -> a/b, True -> \\frac{a}{b}).
"""

from linprog import latex, parse_problem, two_phase

from . import join_blocks

# --- The model (exact Fractions; the parser is forgiving) -------------------

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
            r"    \item \textbf{Formular} el problema correspondiente a la primera fase.",
            r"    \item \textbf{Resolver} el problema $P$ mediante el método de las dos fases.",
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
        sol.message,  # empty when optimal; Spanish sentence otherwise
    )
