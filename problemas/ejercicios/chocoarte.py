# -*- coding: utf-8 -*-
"""ChocoArte: applied production-mix problem (chocolate workshop).

Designed to evaluate understanding without repetitive pivoting: the optimal
basis (x_2, x_3, h_3) is GIVEN in the statement, so the student rebuilds the
optimal tableau via B^{-1} (0 pivots), justifies optimality, does sensitivity,
and re-optimises after adding x_3 <= 8 with exactly ONE dual-simplex pivot.

Designed numbers: optimum x_2 = 20, x_3 = 10, z = 1050; pi = (15, 15/2, 0);
cocoa range [30, 60]; after adding x_3 <= 8: h_4 = -2 forces one Lemke pivot
(h_1 enters, the only negative entry) -> x_2 = 22, x_3 = 8, z = 1020.
"""

from linprog import Basis, dual_simplex, latex, parse_problem, sensitivity

from . import join_blocks

problem = parse_problem(
    """
    max 25x_1 + 30x_2 + 45x_3
    x_1 + x_2 + 2x_3 <= 40
    2x_1 + 2x_2 + 2x_3 <= 60
    x_1 + x_2 + x_3 >= 12
    """
)

# The same problem with the post-optimisation constraint of question 5.
extended = parse_problem(
    """
    max 25x_1 + 30x_2 + 45x_3
    x_1 + x_2 + 2x_3 <= 40
    2x_1 + 2x_2 + 2x_3 <= 60
    x_1 + x_2 + x_3 >= 12
    x_3 <= 8
    """
)

OPTIMAL_BASIS = ["x_2", "x_3", "h_3"]


def statement() -> str:
    return join_blocks(
        r"El obrador artesano \textbf{ChocoArte} elabora y comercializa tres"
        r" productos por lotes: \textbf{tabletas clásicas (T)}, \textbf{cajas de"
        r" bombones (B)} y \textbf{figuras de chocolate (F)}. Los lotes pueden ser"
        r" fraccionados (medio lote, un cuarto de lote, etc.). Por cada lote, el"
        r" obrador obtiene un beneficio neto de \textbf{25, 30 y 45 euros},"
        r" respectivamente.",

        r"Cada semana el obrador dispone de \textbf{40 kg de cacao}: un lote de"
        r" tabletas o de bombones consume \textbf{1 kg}, mientras que un lote de"
        r" figuras, por su mayor tamaño, consume \textbf{2 kg}. Además, la"
        r" elaboración de cualquier lote (atemperado, moldeado y envasado) ocupa"
        r" \textbf{2 horas de obrador}, y la disponibilidad semanal es de"
        r" \textbf{60 horas}.",

        r"Por otra parte, ChocoArte tiene un compromiso con una cadena de"
        r" pastelerías por el que debe suministrar en total \textbf{al menos 12"
        r" lotes semanales}, entre los tres productos.",

        r"El modelo de programación lineal que permite determinar el plan de"
        r" producción semanal óptimo es el siguiente, donde $x_1$, $x_2$ y $x_3$"
        r" representan los lotes semanales de tabletas, bombones y figuras,"
        r" respectivamente:",

        latex.problem_tex(problem),

        r"Se pide:",

        "\n".join([
            r"\begin{enumerate}",
            r"    \item \textbf{Formular} el problema equivalente en formato"
            r" estándar y el problema correspondiente a la primera fase del"
            r" método de las dos fases.",
            r"    \item Se sabe que en la solución óptima se producen bombones y"
            r" figuras y que el compromiso con la cadena de pastelerías se supera"
            r" con holgura, es decir, que las variables básicas son $x_2$, $x_3$"
            r" y $h_3$. \textbf{Construir}, mediante el método de la matriz"
            r" completa y sin realizar iteraciones, la tabla del símplex asociada"
            r" a esa base, indicando $B$, $B^{-1}$, el valor de las variables"
            r" básicas y el beneficio semanal.",
            r"    \item \textbf{Justificar}, mediante el criterio del simplex,"
            r" que la base anterior es efectivamente óptima, calculando los"
            r" multiplicadores del símplex y los costes reducidos.",
            r"    \item \textbf{Interpretar} económicamente el precio sombra del"
            r" cacao (¿interesaría comprar cacao adicional y hasta qué precio por"
            r" kilogramo?) y \textbf{calcular} el rango dentro del cual puede"
            r" variar la disponibilidad semanal de cacao sin que cambie la gama"
            r" de productos de la solución óptima.",
            r"    \item Por limitaciones de moldes, el obrador estudia limitar la"
            r" producción de figuras a un máximo de \textbf{8 lotes semanales}"
            r" ($x_3 \leq 8$). \textbf{Incorporar} esta restricción a la tabla"
            r" óptima y obtener el nuevo plan de producción aplicando el método"
            r" de Lemke (símplex dual), interpretando el efecto sobre el"
            r" beneficio.",
            r"\end{enumerate}",
        ]),
    )


def solution() -> str:
    sf = problem.standard()
    opt = Basis(sf, [sf.variables.index(name) for name in OPTIMAL_BASIS])
    values = opt.values()
    pi_cacao, pi_horas, pi_compromiso = opt.pi
    b1_range = sensitivity.rhs_range(opt, 0)

    # Question 5: dual simplex on the extended problem, starting from the
    # optimal basis plus the new constraint's slack h_4.
    sf_ext = extended.standard()
    start = [sf_ext.variables.index(name) for name in [*OPTIMAL_BASIS, "h_4"]]
    post = dual_simplex(sf_ext, start=start)
    post_values = post.values

    item_1 = join_blocks(
        r"\item \textbf{Formulación en formato estándar y de la primera fase.}",
        r"En formato estándar, las dos primeras restricciones incorporan"
        r" variables de holgura ($h_1$, $h_2$) y la de compromiso una variable"
        r" de exceso ($h_3$):",
        latex.standard_form_tex(sf),
        r"La restricción de compromiso no aporta una variable básica inicial"
        r" (su holgura entra con signo negativo), por lo que se añade la"
        r" variable artificial $a_3$ y la primera fase minimiza su valor:",
        latex.phase1_tex(sf),
    )

    item_2 = join_blocks(
        r"\item \textbf{Tabla óptima mediante el método de la matriz completa.}"
        r" La base propuesta está formada por las columnas de $x_2$, $x_3$ y"
        r" $h_3$ en la matriz de coeficientes del problema estándar:",
        latex.basis_matrix_tex(opt),
        latex.basis_inverse_tex(opt, frac=True),
        r"Los valores de las variables básicas y el beneficio se obtienen"
        r" directamente de la inversa:",
        latex.objective_value_tex(opt),
        rf"Es decir, $u^B = B^{{-1}}b \geq 0$ (solución factible) con"
        rf" $x_2 = {latex.fmt(values['x_2'])}$, $x_3 = {latex.fmt(values['x_3'])}$,"
        rf" $h_3 = {latex.fmt(values['h_3'])}$ y beneficio semanal"
        rf" $z = {latex.fmt(opt.z)}$ euros. La tabla asociada a la base es:",
        latex.tableau([opt], frac=True),
    )

    item_3 = join_blocks(
        r"\item \textbf{Optimalidad mediante el criterio del simplex.} Los"
        r" multiplicadores del símplex y los costes reducidos de la base son:",
        latex.shadow_prices_tex(opt, verbose=True, frac=True),
        latex.reduced_costs_tex(opt, verbose=True, frac=True),
        rf"Todos los costes reducidos son no positivos ($V^B \leq 0$), por lo"
        rf" que la base es óptima. En particular,"
        rf" $V^B_{{x_1}} = {latex.fmt(opt.V[0])}$: producir tabletas clásicas"
        r" empeoraría el beneficio, porque consumen los mismos recursos que los"
        r" bombones (1 kg de cacao y 2 horas por lote) con menor beneficio"
        r" unitario.",
    )

    item_4 = join_blocks(
        r"\item \textbf{Precio sombra del cacao y rango de disponibilidad.}",
        rf"El precio sombra del cacao es $\pi^B_1 = {latex.fmt(pi_cacao)}$: cada"
        rf" kilogramo adicional aumentaría el beneficio en"
        rf" {latex.fmt(pi_cacao)} euros, por lo que al obrador le interesa"
        rf" comprar cacao adicional siempre que el sobreprecio por kilogramo no"
        rf" supere los {latex.fmt(pi_cacao)} euros. (El de las horas es"
        rf" $\pi^B_2 = {latex.fmt(pi_horas)}$ y el del compromiso,"
        rf" $\pi^B_3 = {latex.fmt(pi_compromiso)}$, por no estar saturada esa"
        r" restricción.)",
        r"Para el rango se admite una disponibilidad genérica $b_1$ y se exige"
        r" que la solución básica siga siendo factible:",
        sensitivity.rhs_range_tex(opt, 0, frac=True),
        rf"Mientras la disponibilidad semanal de cacao se mantenga entre"
        rf" {latex.fmt(b1_range.lower)} y {latex.fmt(b1_range.upper)} kg, las"
        r" variables básicas de la solución óptima —y, por lo tanto, la gama de"
        r" productos— no cambian.",
    )

    item_5 = join_blocks(
        r"\item \textbf{Post-optimización con $x_3 \leq 8$ (método de Lemke).}"
        r" Se añade la restricción con su holgura, $x_3 + h_4 = 8$, y se"
        r" incorpora a la tabla óptima tomando $h_4$ como variable básica de la"
        r" nueva fila. Como $x_3 = 10 > 8$, resulta $h_4 = -2 < 0$: la base"
        r" sigue cumpliendo el criterio de optimalidad pero deja de ser"
        r" factible, exactamente la situación que resuelve el método de Lemke:",
        latex.tableau(post.bases, include_artificials=False, frac=True),
        rf"Sale de la base $h_4$ (única componente negativa) y entra $h_1$, la"
        rf" única columna con elemento negativo en su fila. El nuevo plan"
        rf" óptimo es $x_2 = {latex.fmt(post_values['x_2'])}$,"
        rf" $x_3 = {latex.fmt(post_values['x_3'])}$ y"
        rf" $x_1 = {latex.fmt(post_values['x_1'])}$, con beneficio"
        rf" $z = {latex.fmt(post.z)}$ euros: limitar las figuras cuesta"
        rf" {latex.fmt(opt.z - post.z)} euros semanales. Ahora sobra cacao"
        r" (la holgura $h_1$ es básica y positiva) y su precio sombra pasa a"
        r" ser cero.",
    )

    return join_blocks(
        r"\begin{enumerate}",
        item_1, item_2, item_3, item_4, item_5,
        r"\end{enumerate}",
    )
