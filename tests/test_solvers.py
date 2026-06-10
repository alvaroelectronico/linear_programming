"""Regression tests pinning the known textbook results."""

from fractions import Fraction

from linprog import LinearProgram
from linprog.parsing import (
    build_standard_form,
    canonical_var,
    parse_linear_expression,
)


def test_two_phase_simplex_solution():
    problem = LinearProgram(
        objective=("max", "3x_1 + 2x_2 + 1x_3 + 2x_4"),
        constraints=[
            "1x_1 + 3x_2 + 0x_3 = 60",
            "2x_1 + 1x_2 + 3x_3 + 1x_4 <= 100",
            "2x_1 + 1x_2 + 1x_3 >= 50",
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
        objective=("min", "3x_1 + 2x_2"),
        constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
        method="lemke",
    )
    assert problem.solution == {"x_1": Fraction(0), "x_2": Fraction(20)}
    assert problem.bases == [[2, 3], [1, 3]]


def test_formulation_tex_is_stable():
    problem = LinearProgram(
        objective=("max", "3x_1 + 2x_2"),
        constraints=["2x_1 + 4x_2 <= 80"],
    )
    tex = problem.formulation_tex()
    assert tex.startswith("\\begin{equation}")
    assert "\\mbox{max. } z = 3x_1 + 2x_2" in tex
    assert "\\leq" in tex


# --- flexible parsing -----------------------------------------------------


def test_canonical_var_normalisation():
    assert canonical_var("x") == "x"
    assert canonical_var("x1") == "x_1"
    assert canonical_var("x_1") == "x_1"
    assert canonical_var("y") == "y"


def test_parse_linear_expression_implicit_and_fraction_coeffs():
    coeffs = parse_linear_expression("x - 2y + 3/2z")
    assert coeffs == {"x": Fraction(1), "y": Fraction(-2), "z": Fraction(3, 2)}


def test_any_letter_variables_no_spaces_inferred_count():
    problem = LinearProgram(
        objective=("max", "2x+3y"),
        constraints=["x+y<=4", "x+3y<=6"],
    )
    assert problem.standard_form.num_vars == 2
    assert problem.standard_form.variables == ["x", "y"]
    assert problem.solution == {"x": Fraction(3), "y": Fraction(1)}


def test_subscript_optional_is_same_variable():
    # "x1" and "x_1" must denote the same canonical variable.
    sf = build_standard_form(
        constraints=["x1 + x_2 <= 5"],
        objective_function=("max", "x_1 + x2"),
    )
    assert sf.variables == ["x_1", "x_2"]
    assert sf.num_vars == 2


def test_variables_and_constants_on_both_sides():
    # "2x + 3 <= x + 10" normalises to "x <= 7".
    problem = LinearProgram(objective=("max", "x"), constraints=["2x + 3 <= x + 10"])
    assert problem.solution == {"x": Fraction(7)}
