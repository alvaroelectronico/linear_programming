from fractions import Fraction

import pytest

from linprog import parse_problem

F = Fraction


def test_no_factible_standard_form(no_factible_a):
    sf = no_factible_a.standard()
    # >= row 1 -> -h_1 + a_1; = row 2 -> a_2; <= row 3 -> +h_3
    assert sf.variables == ["x_1", "x_2", "x_3", "h_1", "h_3", "a_1", "a_2"]
    assert sf.slack_vars == ["h_1", "h_3"]
    assert sf.artificial_vars == ["a_1", "a_2"]
    assert sf.artificial_rows == [0, 1]
    assert sf.b == [F(80), F(60), F(15)]
    assert sf.A == [
        [F(2), F(4), F(2), F(-1), F(0), F(1), F(0)],
        [F(4), F(3), F(0), F(0), F(0), F(0), F(1)],
        [F(1), F(1), F(1), F(0), F(1), F(0), F(0)],
    ]
    assert sf.c == [F(3), F(2), F(1), F(0), F(0), F(0), F(0)]
    assert sf.needs_two_phase()
    # initial basis: a_1 (col 5), a_2 (col 6), h_3 (col 4)
    assert sf.initial_basis() == [5, 6, 4]
    assert sf.phase1_c() == [F(0)] * 5 + [F(-1), F(-1)]


def test_min_is_negated_to_max_form(lemke_min):
    sf = lemke_min.standard()
    assert sf.c[:3] == [F(-10), F(-20), F(-30)]
    assert sf.problem.goal == "min"  # original preserved for rendering
    assert sf.slack_vars == ["h_1", "h_2", "h_3"]
    assert sf.slack_basis() == [3, 4, 5]
    # the >= row keeps its -1 surplus and positive rhs
    assert sf.A[2][5] == F(-1)
    assert sf.b[2] == F(500)


def test_all_leq_needs_no_artificials():
    sf = parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6").standard()
    assert sf.artificial_vars == []
    assert not sf.needs_two_phase()
    assert sf.initial_basis() == sf.slack_basis() == [2, 3]


def test_negative_rhs_row_is_negated():
    # x - y <= -5  ->  -x + y >= 5 (with artificial)
    sf = parse_problem("max x + y\nx - y <= -5").standard()
    assert sf.b == [F(5)]
    assert sf.A[0][:2] == [F(-1), F(1)]
    assert sf.slack_vars == ["h_1"]
    assert sf.A[0][2] == F(-1)  # surplus
    assert sf.artificial_vars == ["a_1"]


def test_slack_basis_rejects_equalities(dos_fases_a):
    with pytest.raises(ValueError):
        dos_fases_a.standard().slack_basis()


def test_dos_fases_a_columns(dos_fases_a):
    sf = dos_fases_a.standard()
    # = row 1 -> a_1; <= row 2 -> h_2  (slacks named by row, as in the exams)
    assert sf.variables == ["x_1", "x_2", "h_2", "a_1"]
    assert sf.initial_basis() == [3, 2]
