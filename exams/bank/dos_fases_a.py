"""Ejemplo/plantilla: problema de dos fases (dos_fases_a).

Copia este archivo para crear un ejercicio nuevo:

  1. Duplica este módulo en exams/bank/ con el nombre del ejercicio, p. ej.
     exams/bank/mi_ejercicio.py  (el nombre del fichero es el id del ejercicio).
  2. Edita build() con tu enunciado, tu modelo y tus preguntas.
  3. Genera los .tex:           lp-exams render mi_ejercicio
       -> escribe exams/ejercicios/mi_ejercicio.tex      (enunciado)
                  exams/ejercicios/mi_ejercicio_sol.tex  (solución, vía linprog)
  4. Inclúyelo donde quieras:
       - Colección:  lp-exams collection --pdf   (incluye todos los pares .tex/_sol.tex)
       - Examen:     añádelo a la lista de items en exams/exams_def/<examen>.py

linprog resuelve el modelo (símplex de dos fases o Lemke) y genera la formulación
y los tableaux en LaTeX; aquí sólo describes el problema de forma declarativa.
"""

from __future__ import annotations

from exams.models import ExamProblem, ProblemSpec

# Texto del enunciado (narrativa). Es LaTeX tal cual; la formulación matemática
# se añade automáticamente debajo a partir de `spec` (ver include_formulation).
STATEMENT = r"""
Dado el siguiente problema, $P$, de programación lineal:
"""


def build() -> ExamProblem:
    return ExamProblem(
        # id: nombre base de los .tex generados (<id>.tex y <id>_sol.tex).
        # Debe coincidir con el nombre del fichero para que `lp-exams render` lo encuentre.
        id="dos_fases_a",
        # title: rótulo que usa la colección como \section.
        title="Dos fases (A)",
        statement=STATEMENT,
        # spec: el modelo, en el mismo formato que acepta linprog.
        #   objective = (sentido, expresión)   sentido contiene "max" o "min".
        #   constraints = lista de strings con <=, >= o = .
        #   method = "simplex" (dos fases) o "lemke".
        # El número de variables se infiere del texto; los coeficientes pueden ser
        # implícitos (x_1 == 1x_1), decimales o fracciones.
        spec=ProblemSpec(
            objective=("max", "1x_1 + 4x_2"),
            constraints=[
                "4x_1 + 2x_2 = 80",
                "2x_1 + 3x_2 <= 60",
            ],
            method="simplex",
        ),
        # statement_label: \label de la ecuación del enunciado (para \eqref).
        statement_label="eq:dos_fases_a",
        # questions: se renderizan como una lista \enumerate bajo el enunciado.
        questions=[
            r"\textbf{Formular} el problema correspondiente a la primera fase "
            r"(método de las dos fases).",
            r"\textbf{Resolver} el problema $P$ mediante el método de la matriz "
            r"completa aplicando el método de las dos fases.",
        ],
        points=10.0,
        # Flags de la solución generada (qué secciones aparecen en el _sol.tex):
        include_formulation=True,   # añade la formulación al ENUNCIADO
        include_phase1=True,        # muestra la formulación de la 1ª fase (si hay artificiales)
        include_tableau=True,       # muestra el/los tableau(x) del símplex
        include_basis_details=False,  # (opcional) B, B^{-1}, pi^B, u^B, v^B por base
    )
