"""Furniture-factory production-mix problem (two-phase simplex)."""

from __future__ import annotations

from exams.models import ExamProblem, ProblemSpec

STATEMENT = r"""
A furniture workshop makes tables ($x_1$) and chairs ($x_2$). Each table needs
3 hours of carpentry and 1 of finishing; each chair needs 2 of carpentry and 2
of finishing. There are 18 carpentry hours and 12 finishing hours available, and
at least 2 tables must be produced. Tables yield a profit of 5 and chairs of 4.
Maximise the total profit.
"""


def build() -> ExamProblem:
    return ExamProblem(
        id="mueblespro",
        title="Furniture workshop",
        statement=STATEMENT,
        spec=ProblemSpec(
            objective=("max", "5x_1 + 4x_2"),
            constraints=[
                "3x_1 + 2x_2 <= 18",
                "1x_1 + 2x_2 <= 12",
                "1x_1 >= 2",
            ],
        ),
        points=6.0,
    )
