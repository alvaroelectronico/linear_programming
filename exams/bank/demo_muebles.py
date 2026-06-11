"""Generated demo problem: production mix solved with two-phase simplex."""

from __future__ import annotations

from exams.models import ExamProblem, ProblemSpec

STATEMENT = r"""
Un taller fabrica \textbf{mesas} ($x_1$) y \textbf{sillas} ($x_2$). Cada mesa deja
un beneficio de 5 u.m. y cada silla de 4 u.m. La carpintería dispone de 18 horas
y el acabado de 12 horas; una mesa consume 3 horas de carpintería y 1 de acabado,
y una silla 2 y 2 respectivamente. Por contrato deben fabricarse al menos 2 mesas.
El modelo que maximiza el beneficio es el siguiente:
"""


def build() -> ExamProblem:
    return ExamProblem(
        id="demo_muebles",
        title="Taller de muebles",
        statement=STATEMENT,
        spec=ProblemSpec(
            objective=("max", "5x_1 + 4x_2"),
            constraints=[
                "3x_1 + 2x_2 <= 18",
                "1x_1 + 2x_2 <= 12",
                "1x_1 >= 2",
            ],
        ),
        statement_label="eq:demo_muebles",
        questions=[
            "Formular el problema de la primera fase del método de las dos fases.",
            "Resolver el problema mediante el método de la matriz completa.",
            "Indicar el plan de producción óptimo y el beneficio alcanzado.",
        ],
        points=6.0,
    )
