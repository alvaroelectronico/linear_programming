"""Plantilla GENÉRICA de ejercicio generado (ejemplo: dos_fases_a).

Un solo módulo describe el problema y genera DOS .tex reutilizando el mismo
problema resuelto:
    lp-exams render dos_fases_a
      -> exams/ejercicios/dos_fases_a.tex      (enunciado: texto + formulación + preguntas)
      -> exams/ejercicios/dos_fases_a_sol.tex  (solución: la construyes tú, abajo)

Para crear un ejercicio nuevo: copia este archivo a exams/bank/<id>.py (el nombre
del fichero es el id), edita el enunciado, el modelo, las preguntas y la función
build_solution(), y ejecuta `lp-exams render <id>`.

------------------------------------------------------------------------------
ELEMENTOS DEL PROBLEMA disponibles en build_solution(prob, frac_command):

  prob.formulation_tex()                 formulación del problema original
  prob.formulation_phase1_tex()          formulación de la primera fase
  prob.compose_tableau(bases, ...)       tabla(s) del símplex para una lista de bases
  prob.basic_solutions                   lista de soluciones básicas visitadas (en orden)
  prob.optimal_basic_solution            la solución básica óptima (la última)
  prob.solution                          dict {"x_1": Fraction, ...} con la solución óptima
  prob.result.objective_value            valor de z en la última tabla
  prob.result.bases / first_feasible_base / optimal_base
  prob.standard_form                     A, b, c1, c2, variables, var_names, ...

  Cada solución básica (p. ej. bs = prob.optimal_basic_solution) ofrece, en LaTeX:
     bs.B_tex()      bs.invB_tex()    bs.pB_tex()        (B, B^{-1}, B^{-1}A)
     bs.uB_tex()     bs.piB_tex()     bs.vB_tex()        (u^B, pi^B, costes reducidos)
     bs.zB_uB_tex()  bs.zB_x_tex()                       (valor objetivo de dos formas)
     bs.tableau_basic_sol_tex()                          (su fila de la tabla)
  ...y los arrays numéricos (Fraction): bs.B, bs.invB, bs.piB, bs.uB, bs.vB, bs.z

  Todos los *_tex aceptan frac_command=... (\\frac{a}{b} vs a/b). Pásale el
  frac_command que recibe build_solution para respetar la opción --frac/--no-frac.
------------------------------------------------------------------------------
"""

from __future__ import annotations

from linprog.reporting import fraction_to_tex

from exams.models import ExamProblem, ProblemSpec

STATEMENT = r"""
Dado el siguiente problema, $P$, de programación lineal:
"""


def build_solution(prob, frac_command: bool = True) -> str:
    """Construye el cuerpo del .tex de solución a partir de los elementos de `prob`.

    Es sólo un ejemplo: reordena, quita o añade lo que necesite cada ejercicio.
    """
    opt = prob.optimal_basic_solution
    solucion = ", ".join(
        f"$x_{{{k.split('_')[1]}}} = {fraction_to_tex(v, frac_command=frac_command)}$"
        if "_" in k
        else f"${k} = {fraction_to_tex(v, frac_command=frac_command)}$"
        for k, v in sorted(prob.solution.items())
    )

    bloques = [
        r"\textbf{Formulación de la primera fase}",
        prob.formulation_phase1_tex(),

        r"\textbf{Resolución mediante el método de las dos fases}",
        prob.compose_tableau(prob.basic_solutions, frac_command=frac_command),

        r"\textbf{Base óptima y su inversa}",
        opt.B_tex(frac_command=frac_command),
        opt.invB_tex(frac_command=frac_command),

        r"\textbf{Multiplicadores del símplex y costes reducidos}",
        opt.piB_tex(frac_command=frac_command),
        opt.vB_tex(frac_command=frac_command),

        r"\textbf{Valor de la función objetivo}",
        opt.zB_uB_tex(frac_command=frac_command),

        rf"\textbf{{Solución óptima:}} {solucion}.",
    ]
    return "\n\n".join(bloques) + "\n"


def build() -> ExamProblem:
    return ExamProblem(
        id="dos_fases_a",
        title="Dos fases (A)",
        # spec: el modelo, en el formato que acepta linprog (objetivo + restricciones).
        spec=ProblemSpec(
            objective=("max", "1x_1 + 4x_2"),
            constraints=[
                "4x_1 + 2x_2 = 80",
                "2x_1 + 3x_2 <= 60",
            ],
            method="simplex",
        ),
        # --- Enunciado -------------------------------------------------------
        statement=STATEMENT,
        include_formulation=True,            # añade la formulación tras el texto
        statement_label="eq:dos_fases_a",    # \label de la ecuación (para \eqref)
        questions=[
            r"\textbf{Formular} el problema correspondiente a la primera fase "
            r"(método de las dos fases).",
            r"\textbf{Resolver} el problema $P$ mediante el método de la matriz "
            r"completa aplicando el método de las dos fases.",
        ],
        points=10.0,
        # --- Solución --------------------------------------------------------
        # Builder a medida (arriba). Si lo dejas en None, se usa el diseño por
        # defecto controlado por include_phase1 / include_tableau / include_basis_details.
        solution_builder=build_solution,
    )
