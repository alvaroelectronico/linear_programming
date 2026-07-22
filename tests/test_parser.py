from fractions import Fraction

import pytest

from linprog import ParseError, parse_problem

F = Fraction


def test_claude_md_example():
    problem = parse_problem(
        """
        max 3x1 + 4x2
        x1+2x2<=50
        x1+x2>=10
        """
    )
    assert problem.goal == "max"
    assert problem.objective == {"x_1": F(3), "x_2": F(4)}
    assert problem.variables == ["x_1", "x_2"]
    assert problem.n_vars == 2
    assert problem.n_constraints == 2
    assert problem.A == [[F(1), F(2)], [F(1), F(1)]]
    assert problem.b == [F(50), F(10)]
    assert problem.c == [F(3), F(4)]
    assert problem.senses == ["<=", ">="]


def test_spaces_are_optional():
    tight = parse_problem("max 2x+3y\nx+y<=4")
    loose = parse_problem("max   2 x + 3 y\n  x + y   <= 4")
    assert tight == loose


def test_x1_equals_x_1():
    problem = parse_problem("max 3x1 + 2x_1\nx_1 <= 5")
    assert problem.objective == {"x_1": F(5)}
    assert problem.variables == ["x_1"]


def test_implicit_and_negative_coefficients():
    problem = parse_problem("max x - y\n-x + y <= 3")
    assert problem.objective == {"x": F(1), "y": F(-1)}
    assert problem.A == [[F(-1), F(1)]]


def test_decimal_and_fraction_coefficients():
    problem = parse_problem("min 2.5x + 3/2y\nx + y >= 1")
    assert problem.goal == "min"
    assert problem.objective == {"x": F(5, 2), "y": F(3, 2)}


def test_all_three_senses():
    problem = parse_problem("max x\nx <= 4\nx >= 1\nx = 2")
    assert problem.senses == ["<=", ">=", "="]


def test_variables_and_constants_on_both_sides():
    # 2x + 3 <= y + 10  ->  2x - y <= 7
    problem = parse_problem("max x + y\n2x + 3 <= y + 10")
    constraint = problem.constraints[0]
    assert constraint.coeffs == {"x": F(2), "y": F(-1)}
    assert constraint.rhs == F(7)


def test_objective_with_z_prefix():
    problem = parse_problem("max z = 3x + 4y\nx + y <= 1")
    assert problem.objective == {"x": F(3), "y": F(4)}


def test_variable_order_objective_first_then_constraints():
    problem = parse_problem("max y + x\nw + x <= 1\nv <= 2")
    assert problem.variables == ["y", "x", "w", "v"]


def test_any_variable_names():
    problem = parse_problem("max 2sillas + 3mesas\nsillas + mesas <= 10")
    assert problem.variables == ["sillas", "mesas"]


def test_min_problem():
    problem = parse_problem("min 3x_1 + 2x_2\n2x_1 + 4x_2 >= 80\n4x_1 + 3x_2 <= 60")
    assert problem.goal == "min"
    assert problem.b == [F(80), F(60)]


def test_repeated_variable_in_expression_is_accumulated():
    problem = parse_problem("max 2x + 3x\nx <= 1")
    assert problem.objective == {"x": F(5)}


@pytest.mark.parametrize(
    "text",
    [
        "",  # empty
        "3x + 4y\nx <= 1",  # missing max/min
        "max 3x + 4y",  # no constraints
        "max 3x + 4y\nx ? 1",  # bad relation
        "max 3x + 4y\nx + <= 1",  # dangling operator
        "max 3x + 4y\n3 <= 1",  # constraint without variables
        "max 3x + 5\nx <= 1",  # constant in the objective
    ],
)
def test_parse_errors(text):
    with pytest.raises(ParseError):
        parse_problem(text)
