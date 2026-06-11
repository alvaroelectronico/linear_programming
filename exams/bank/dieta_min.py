"""Diet (cost-minimisation) problem solved with Lemke's method."""

from __future__ import annotations

from exams.models import ExamProblem, ProblemSpec

STATEMENT = r"""
A diet must supply at least 80 units of protein and at most 60 units of fat,
using two foods $x_1$ and $x_2$. Each unit of $x_1$ provides 2 protein and 4 fat;
each unit of $x_2$ provides 4 protein and 3 fat. The unit costs are 3 and 2.
Minimise the total cost.
"""


def build() -> ExamProblem:
    return ExamProblem(
        id="dieta_min",
        title="Diet problem",
        statement=STATEMENT,
        spec=ProblemSpec(
            objective=("min", "3x_1 + 2x_2"),
            constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
            method="lemke",
        ),
        points=4.0,
        # Lemke output has no two-phase artificials.
        include_phase1=False,
    )
