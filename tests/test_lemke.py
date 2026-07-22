from fractions import Fraction

import pytest

from linprog import latex, parse_problem
from linprog.solvers import MSG_INFEASIBLE, Status, dual_simplex

from conftest import normalize

F = Fraction


def test_split_equalities():
    original = parse_problem(
        "min 10x_1 + 20x_2 + 30x_3\n4x_1 + 2x_2 + 8x_3 <= 1000\nx_2 + x_3 = 500"
    )
    split = original.split_equalities()
    assert split.senses == ["<=", "<=", ">="]
    assert split.constraints[1].coeffs == split.constraints[2].coeffs
    assert split.b == [F(1000), F(500), F(500)]
    assert original.senses == ["<=", "="]  # untouched


def test_lemke_golden_tableau(lemke_min):
    # examples/lemke_sol.tex lines 61-77: two iterations, degenerate optimum
    solution = dual_simplex(lemke_min.standard())
    assert solution.status is Status.OPTIMAL
    assert [basis.names for basis in solution.bases] == [
        ("h_1", "h_2", "h_3"), ("h_1", "h_2", "x_2"),
    ]
    assert solution.degenerate  # h_1 = h_2 = 0 at the optimum
    assert solution.z == F(-10000)          # max form (s in the example)
    assert solution.objective_value == F(10000)  # original min objective
    assert solution.values == {"x_1": F(0), "x_2": F(500), "x_3": F(0)}

    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccccc|}
     & $s$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_2$ & $h_3$\\
     & $0$ & $-10$ & $-20$ & $-30$ & $0$ & $0$ & $0$ \\
    \hline
    $h_1$ & $1000$  & $4$ & $2$ & $8$ & $1$ & $0$ & $0$\\
    $h_2$ & $500$  & $0$ & $1$ & $1$ & $0$ & $1$ & $0$\\
    $h_3$ & $-500$  & $0$ & $-1$ & $-1$ & $0$ & $0$ & $1$\\
    \hline
     & $10000$ & $-10$ & $0$ & $-10$ & $0$ & $0$ & $-20$ \\
    \hline
    $h_1$ & $0$  & $4$ & $0$ & $6$ & $1$ & $0$ & $2$\\
    $h_2$ & $0$  & $0$ & $0$ & $0$ & $0$ & $1$ & $1$\\
    $x_2$ & $500$  & $0$ & $1$ & $1$ & $0$ & $0$ & $-1$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.tableau(
        solution.bases, include_artificials=False, value_label="s"
    )
    assert normalize(rendered) == normalize(expected)


def test_lemke_from_the_original_problem_via_split(lemke_min):
    original = parse_problem(
        "min 10x_1 + 20x_2 + 30x_3\n4x_1 + 2x_2 + 8x_3 <= 1000\nx_2 + x_3 = 500"
    )
    solution = dual_simplex(original.split_equalities().standard())
    assert solution.status is Status.OPTIMAL
    assert solution.objective_value == F(10000)
    # same problem as the pre-split fixture:
    assert solution.values == dual_simplex(lemke_min.standard()).values


def test_dual_simplex_detects_infeasibility():
    solution = dual_simplex(parse_problem("max -x\nx <= 1\nx >= 2").standard())
    assert solution.status is Status.INFEASIBLE
    assert solution.message == MSG_INFEASIBLE


def test_dual_simplex_rejects_positive_reduced_costs():
    sf = parse_problem("max x + y\nx + y <= 4").standard()
    with pytest.raises(ValueError, match="V <= 0"):
        dual_simplex(sf)


def test_dual_simplex_rejects_equality_rows():
    sf = parse_problem("max -x\nx = 2").standard()
    with pytest.raises(ValueError, match="split"):
        dual_simplex(sf)


def test_already_feasible_start_is_optimal_immediately():
    solution = dual_simplex(parse_problem("max -x - y\nx + y <= 4").standard())
    assert solution.status is Status.OPTIMAL
    assert len(solution.bases) == 1
    assert solution.z == F(0)
