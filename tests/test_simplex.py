from fractions import Fraction

import pytest

from linprog import parse_problem
from linprog.solvers import MSG_UNBOUNDED, Status, simplex

F = Fraction


def solve(text):
    return simplex(parse_problem(text).standard())


def test_optimal_basic_max():
    solution = solve("max 2x + 3y\nx + y <= 4\nx + 3y <= 6")
    assert solution.status is Status.OPTIMAL
    assert solution.values == {"x": F(3), "y": F(1)}
    assert solution.z == F(9)
    assert solution.objective_value == F(9)
    assert not solution.degenerate
    assert not solution.alternate_optima
    assert solution.message == ""
    # visited bases: (h_1, h_2) -> (h_1, y) -> (x, y)
    assert [basis.names for basis in solution.bases] == [
        ("h_1", "h_2"), ("h_1", "y"), ("x", "y"),
    ]


def test_min_is_solved_via_max_form():
    solution = solve("min -2x - 3y\nx + y <= 4\nx + 3y <= 6")
    assert solution.status is Status.OPTIMAL
    assert solution.values == {"x": F(3), "y": F(1)}
    assert solution.z == F(9)  # max form, as shown in the tableau
    assert solution.objective_value == F(-9)  # original min objective


def test_unbounded():
    solution = solve("max x\nx - y <= 1")
    assert solution.status is Status.UNBOUNDED
    assert solution.message == MSG_UNBOUNDED
    assert [basis.names for basis in solution.bases] == [("h_1",), ("x",)]


def test_degenerate_path_is_flagged():
    solution = solve("max x + y\nx <= 2\nx + y <= 2")
    assert solution.status is Status.OPTIMAL
    assert solution.degenerate
    assert solution.z == F(2)


def test_alternate_optima_flagged():
    solution = solve("max x + y\nx + y <= 4")
    assert solution.status is Status.OPTIMAL
    assert solution.alternate_optima
    assert solution.z == F(4)


def test_every_visited_basis_is_feasible_and_z_never_decreases():
    solution = solve("max 2x + 3y\nx + y <= 4\nx + 3y <= 6")
    assert all(basis.is_feasible for basis in solution.bases)
    z_values = [basis.z for basis in solution.bases]
    assert z_values == sorted(z_values)
    # sanity: A x = b at the optimum
    sf = solution.final.sf
    values = solution.final.values()
    x = [values[name] for name in sf.variables]
    for row, rhs in zip(sf.A, sf.b):
        assert sum(a * v for a, v in zip(row, x)) == rhs


def test_needs_two_phase_without_start_raises():
    sf = parse_problem("max x\nx >= 2").standard()
    with pytest.raises(ValueError, match="two_phase"):
        simplex(sf)


def test_infeasible_start_raises():
    sf = parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6").standard()
    # basis (x, h_1): row 2 forces x = 6, so row 1 gives h_1 = -2
    with pytest.raises(ValueError, match="not feasible"):
        simplex(sf, start=[0, 2])


def test_explicit_feasible_start_is_respected():
    sf = parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6").standard()
    solution = simplex(sf, start=[0, 1])  # start straight at (x, y)
    assert solution.status is Status.OPTIMAL
    assert len(solution.bases) == 1  # already optimal
    assert solution.z == F(9)
