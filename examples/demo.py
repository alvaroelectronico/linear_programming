"""Runnable examples for the linprog package.

Replaces the old ``__main__`` blocks and the broken ``sandbox_exam.py``. Run
with ``python -m examples.demo`` from the repository root.
"""

from linprog import LinearProgram
from linprog.reporting import latex_document, render_worked_solution


def simplex_example() -> None:
    objective = ("max", "3x_1 + 2y + 1x_3 + 2x_4")
    # Variables omitted from a constraint are taken to have coefficient 0,
    # so there is no need to write terms like "0x_3" or to list x_4 everywhere.
    constraints = [
        "1x_1 + 3y = 60",
        "2x_1 + 1y + 3x_3 + 1x_4 <= 100",
        "2x_1 + 1y + 1x_3 >= 50",
    ]
    problem = LinearProgram(constraints=constraints, objective=objective)

    print("Solution:", dict(sorted(problem.solution.items())))
    print("\nOriginal formulation (LaTeX):")
    print(problem.formulation_tex())
    print("\nPhase-1 formulation (LaTeX):")
    print(problem.formulation_phase1_tex())
    print("\nFull tableau (LaTeX):")
    print(problem.compose_tableau(problem.basic_solutions))


def lemke_example() -> None:
    objective = ("min", "3x_1 + 2x_2")
    constraints = ["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"]
    problem = LinearProgram(constraints=constraints, objective=objective, method="lemke")
    print("Lemke solution:", dict(sorted(problem.solution.items())))


def flexible_syntax_example() -> None:
    """Any-letter variables, no spaces, inferred variable count."""
    problem = LinearProgram(
        objective=("max", "2x+3y"),
        constraints=["x+y<=4", "x+3y<=6"],
    )
    print("Flexible-syntax solution:", dict(sorted(problem.solution.items())))


def worked_solution_example() -> None:
    """Assemble a full, compilable LaTeX document for a solved problem."""
    problem = LinearProgram(
        objective=("max", "5x_1 + 4x_2"),
        constraints=["3x_1 + 2x_2 <= 18", "1x_1 + 2x_2 <= 12"],
    )
    body = render_worked_solution(problem)
    document = latex_document(body, title="Worked solution")
    print("Standalone LaTeX document (first lines):")
    print("\n".join(document.splitlines()[:6]))


if __name__ == "__main__":
    simplex_example()
    print("\n" + "=" * 60 + "\n")
    lemke_example()
    print("\n" + "=" * 60 + "\n")
    flexible_syntax_example()
    print("\n" + "=" * 60 + "\n")
    worked_solution_example()
