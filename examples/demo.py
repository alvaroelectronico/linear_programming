"""Runnable examples for the linprog package.

Replaces the old ``__main__`` blocks and the broken ``sandbox_exam.py``. Run
with ``python -m examples.demo`` from the repository root.
"""

from linprog import LinearProgram


def simplex_example() -> None:
    objective = ("max", "3x_1 + 2x_2 + 1x_3 + 2x_4")
    constraints = [
        "1x_1 + 3x_2 + 0x_3 = 60",
        "2x_1 + 1x_2 + 3x_3 + 1x_4 <= 100",
        "2x_1 + 1x_2 + 1x_3 -5x4 >= 50",
    ]
    problem = LinearProgram(num_vars=4, constraints=constraints, objective=objective)

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
    problem = LinearProgram(num_vars=2, constraints=constraints, objective=objective, method="lemke")
    print("Lemke solution:", dict(sorted(problem.solution.items())))


if __name__ == "__main__":
    simplex_example()
    print("\n" + "=" * 60 + "\n")
    lemke_example()
