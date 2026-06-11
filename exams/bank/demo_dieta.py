"""Generated demo problem: diet (cost minimisation) solved with Lemke's method."""

from __future__ import annotations

from exams.models import ExamProblem, ProblemSpec

STATEMENT = r"""
Una dieta debe aportar al menos 80 unidades de proteína usando dos alimentos
$x_1$ y $x_2$, sin superar 60 unidades de grasa. Cada unidad de $x_1$ aporta 2 de
proteína y 4 de grasa; cada unidad de $x_2$, 4 de proteína y 3 de grasa. Los
costes unitarios son 3 y 2. El modelo que minimiza el coste es:
"""


def build() -> ExamProblem:
    return ExamProblem(
        id="demo_dieta",
        title="Problema de la dieta",
        statement=STATEMENT,
        spec=ProblemSpec(
            objective=("min", "3x_1 + 2x_2"),
            constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
            method="lemke",
        ),
        statement_label="eq:demo_dieta",
        questions=["Resolver el problema mediante el método de Lemke."],
        points=4.0,
        include_phase1=False,  # Lemke has no two-phase artificials
    )
