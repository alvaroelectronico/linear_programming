"""Regression tests pinning the known textbook results."""

from fractions import Fraction

from linprog import LinearProgram


def test_two_phase_simplex_solution():
    problem = LinearProgram(
        num_vars=4,
        objective=("max", "3x_1 + 2x_2 + 1x_3 + 2x_4"),
        constraints=[
            "1x_1 + 3x_2 + 0x_3 = 60",
            "2x_1 + 1x_2 + 3x_3 + 1x_4 <= 100",
            "2x_1 + 1x_2 + 1x_3 -5x4 >= 50",
        ],
    )
    assert problem.solution == {
        "x_1": Fraction(18),
        "x_2": Fraction(14),
        "x_3": Fraction(0),
        "x_4": Fraction(50),
    }
    # Objective value: 3*18 + 2*14 + 0 + 2*50 = 182.
    assert problem.result.objective_value == -182


def test_lemke_solution():
    problem = LinearProgram(
        num_vars=2,
        objective=("min", "3x_1 + 2x_2"),
        constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
        method="lemke",
    )
    assert problem.solution == {"x_1": Fraction(0), "x_2": Fraction(20)}
    assert problem.bases == [[2, 3], [1, 3]]


def test_formulation_tex_is_stable():
    problem = LinearProgram(
        num_vars=2,
        objective=("max", "3x_1 + 2x_2"),
        constraints=["2x_1 + 4x_2 <= 80"],
    )
    tex = problem.formulation_tex()
    assert tex.startswith("\\begin{equation}")
    assert "\\mbox{max. } z = 3x_1 + 2x_2" in tex
    assert "\\leq" in tex
