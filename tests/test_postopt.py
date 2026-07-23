from fractions import Fraction

import pytest

from linprog import Basis, Status, latex, parse_problem, postoptimize, two_phase

from conftest import normalize

F = Fraction


def cargoplan_basis(cargoplan):
    sf = cargoplan.standard()
    basis = Basis(sf, [sf.variables.index(name) for name in ("h_1", "h_3", "x_2")])
    assert basis.is_optimal and basis.z == F(60000)
    return basis


def test_add_constraints_appends_and_preserves():
    problem = parse_problem("max x + y\nx + y <= 4")
    extended = problem.add_constraints("x <= 2", "x - y = 1")
    assert extended.senses == ["<=", "<=", "="]
    assert extended.constraints[2].coeffs == {"x": F(1), "y": F(-1)}
    assert problem.n_constraints == 1  # original untouched


def test_postoptimize_infeasible_case_golden(cargoplan):
    # examples/cargoplan_a_sol.tex lines 220-266: add x_1 = x_2 (split into
    # h_4 / h_5), h_5 = -1500 forces ONE Lemke pivot -> z = 54000.
    post = postoptimize(cargoplan_basis(cargoplan), "x_1 = x_2")
    assert list(post.new_rows) == [3, 4]
    assert not post.was_feasible
    assert post.initial.names == ("h_1", "h_3", "x_2", "h_4", "h_5")
    assert post.initial.values()["h_5"] == F(-1500)

    solution = post.solution
    assert solution.status is Status.OPTIMAL
    assert len(solution.bases) == 2  # exactly one pivot
    assert solution.final.names == ("h_1", "h_3", "x_2", "h_4", "x_1")
    assert solution.z == F(54000)
    assert solution.values == {"x_1": F(600), "x_2": F(600), "x_3": F(0)}
    assert solution.final.values()["h_3"] == F(100)
    assert solution.degenerate  # h_4 stays basic at 0


def test_postoptimize_feasible_case(cargoplan):
    # cargoplan question: "at least as much to zone A as to zone C" — the old
    # plan (x_1 = x_3 = 0) already satisfies it.
    post = postoptimize(cargoplan_basis(cargoplan), "x_1 >= x_3")
    assert post.was_feasible
    assert post.solution.status is Status.OPTIMAL
    assert len(post.solution.bases) == 1
    assert post.solution.z == F(60000)


def test_postoptimize_requires_optimal_basis(cargoplan):
    sf = cargoplan.standard()
    slacks = Basis(sf, sf.initial_basis())
    with pytest.raises(ValueError, match="optimal"):
        postoptimize(slacks, "x_1 <= 10")


def test_postoptimize_chocoarte_matches_manual_flow():
    # The chocoarte exercise did this by hand; the API must agree.
    problem = parse_problem(
        "max 25x_1 + 30x_2 + 45x_3\n"
        "x_1 + x_2 + 2x_3 <= 40\n2x_1 + 2x_2 + 2x_3 <= 60\nx_1 + x_2 + x_3 >= 12"
    )
    optimal = two_phase(problem.standard()).final
    post = postoptimize(optimal, "x_3 <= 8")
    assert not post.was_feasible
    assert post.solution.z == F(1020)
    assert post.solution.values == {"x_1": F(0), "x_2": F(22), "x_3": F(8)}


def test_introduce_rows_tex_golden(cargoplan):
    # examples/cargoplan_a_sol.tex lines 224-237 (commented block): old basis
    # over the extended columns, raw new rows, then the eliminated rows.
    post = postoptimize(cargoplan_basis(cargoplan), "x_1 = x_2")
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccccccc|}
     & $z$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_2$ & $h_3$ & $h_4$ & $h_5$\\
     & $-60000$ & $-10$ & $0$ & $-40$ & $0$ & $-20$ & $0$ & $0$ & $0$\\
    \hline
    $h_1$ & $2000$  & $0$ & $0$ & $-2$ & $1$ & $-2$ & $0$ & $0$ & $0$\\
    $h_3$ & $1000$  & $3/2$ & $0$ & $3/2$ & $0$ & $1/2$ & $1$ & $0$ & $0$\\
    $x_2$ & $1500$  & $3/2$ & $1$ & $5/2$ & $0$ & $1/2$ & $0$ & $0$ & $0$\\
    \hline
     & $0$  & $1$ & $-1$ & $0$ & $0$ & $0$ & $0$ & $1$ & $0$\\
     & $0$  & $1$ & $-1$ & $0$ & $0$ & $0$ & $0$ & $0$ & $-1$\\
    \hline
    $h_4$ & $1500$  & $5/2$ & $0$ & $5/2$ & $0$ & $1/2$ & $0$ & $1$ & $0$\\
    $h_5$ & $-1500$ & $-5/2$ & $0$ & $-5/2$ & $0$ & $-1/2$ & $0$ & $0$ & $1$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.introduce_rows_tex(post, include_artificials=False)
    assert normalize(rendered) == normalize(expected)


def test_reoptimization_tableau_golden(cargoplan):
    # examples/cargoplan_a_sol.tex lines 239-257: extended tableau + one
    # Lemke iteration to the new optimum.
    post = postoptimize(cargoplan_basis(cargoplan), "x_1 = x_2")
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccccccc|}
     & $z$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_2$ & $h_3$ & $h_4$ & $h_5$\\
     & $-60000$ & $-10$ & $0$ & $-40$ & $0$ & $-20$ & $0$ & $0$ & $0$\\
    \hline
    $h_1$ & $2000$  & $0$ & $0$ & $-2$ & $1$ & $-2$ & $0$ & $0$ & $0$\\
    $h_3$ & $1000$  & $3/2$ & $0$ & $3/2$ & $0$ & $1/2$ & $1$ & $0$ & $0$\\
    $x_2$ & $1500$  & $3/2$ & $1$ & $5/2$ & $0$ & $1/2$ & $0$ & $0$ & $0$\\
    $h_4$ & $1500$  & $5/2$ & $0$ & $5/2$ & $0$ & $1/2$ & $0$ & $1$ & $0$\\
    $h_5$ & $-1500$ & $-5/2$ & $0$ & $-5/2$ & $0$ & $-1/2$ & $0$ & $0$ & $1$\\
    \hline
     & $-54000$ & $0$ & $0$ & $-30$ & $0$ & $-18$ & $0$ & $0$ & $-4$ \\
    \hline
    $h_1$ & $2000$  & $0$ & $0$ & $-2$ & $1$ & $-2$ & $0$ & $0$ & $0$\\
    $h_3$ & $100$  & $0$ & $0$ & $0$ & $0$ & $1/5$ & $1$ & $0$ & $3/5$\\
    $x_2$ & $600$  & $0$ & $1$ & $1$ & $0$ & $1/5$ & $0$ & $0$ & $3/5$\\
    $h_4$ & $0$  & $0$ & $0$ & $0$ & $0$ & $0$ & $0$ & $1$ & $1$\\
    $x_1$ & $600$  & $1$ & $0$ & $1$ & $0$ & $1/5$ & $0$ & $0$ & $-2/5$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.tableau(post.solution.bases, include_artificials=False)
    assert normalize(rendered) == normalize(expected)
