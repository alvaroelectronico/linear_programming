from fractions import Fraction

from linprog import latex, parse_problem
from linprog.solvers import MSG_INFEASIBLE, MSG_UNBOUNDED, Status, two_phase

from conftest import normalize

F = Fraction


def test_dos_fases_a_full_tableau_golden(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 14-35 — the strongest checkpoint:
    # the whole stacked two-phase tableau, reproduced exactly.
    solution = two_phase(dos_fases_a.standard())
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccc|}
     & $z$ & $x_1$ & $x_2$ & $h_2$ & $a_1$\\
    Fase 1 & $80$ & $4$ & $2$ & $0$ & $0$ \\
    Fase 2 & $0$ & $1$ & $4$ & $0$ & $0$ \\
    \hline
    $a_1$ & $80$  & $4$ & $2$ & $0$ & $1$\\
    $h_2$ & $60$  & $2$ & $3$ & $1$ & $0$\\
    \hline
    Fase 1 & $0$ & $0$ & $0$ & $0$ & $-1$ \\
    Fase 2 & $-20$ & $0$ & $\frac{7}{2}$ & $0$ & $\frac{-1}{4}$ \\
    \hline
    $x_1$ & $20$  & $1$ & $\frac{1}{2}$ & $0$ & $\frac{1}{4}$\\
    $h_2$ & $20$  & $0$ & $2$ & $1$ & $\frac{-1}{2}$\\
    \hline
    Fase 2 & $-55$ & $0$ & $0$ & $\frac{-7}{4}$ & $\frac{5}{8}$ \\
    \hline
    $x_1$ & $15$  & $1$ & $0$ & $\frac{-1}{4}$ & $\frac{3}{8}$\\
    $x_2$ & $10$  & $0$ & $1$ & $\frac{1}{2}$ & $\frac{-1}{4}$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.tableau(
        solution.bases, two_phase_split=solution.phase1_end, frac=True
    )
    assert normalize(rendered) == normalize(expected)

    assert solution.status is Status.OPTIMAL
    assert solution.phase1_end == 2
    assert solution.values == {"x_1": F(15), "x_2": F(10)}
    assert solution.z == F(55)
    assert [basis.names for basis in solution.bases] == [
        ("a_1", "h_2"), ("x_1", "h_2"), ("x_1", "x_2"),
    ]


def test_infeasible_golden(no_factible_a):
    # examples/dos_fases_no_factible_a_sol.tex lines 45-65
    solution = two_phase(no_factible_a.standard())
    assert solution.status is Status.INFEASIBLE
    assert solution.message == MSG_INFEASIBLE
    assert solution.phase1_end == len(solution.bases) == 2
    assert [basis.names for basis in solution.bases] == [
        ("a_1", "a_2", "h_3"), ("a_1", "a_2", "x_2"),
    ]
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|ccccccc|}
     & $z$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_3$ & $a_1$ & $a_2$\\
    Fase 1 & $140$ & $6$ & $7$ & $2$ & $-1$ & $0$ & $0$ & $0$ \\
    Fase 2 & $0$ & $3$ & $2$ & $1$ & $0$ & $0$ & $0$ & $0$ \\
    \hline
    $a_1$ & $80$  & $2$ & $4$ & $2$ & $-1$ & $0$ & $1$ & $0$\\
    $a_2$ & $60$  & $4$ & $3$ & $0$ & $0$ & $0$ & $0$ & $1$\\
    $h_3$ & $15$  & $1$ & $1$ & $1$ & $0$ & $1$ & $0$ & $0$\\
    \hline
    Fase 1 & $35$ & $-1$ & $0$ & $-5$ & $-1$ & $-7$ & $0$ & $0$ \\
    Fase 2 & $-30$ & $1$ & $0$ & $-1$ & $0$ & $-2$ & $0$ & $0$ \\
    \hline
    $a_1$ & $20$  & $-2$ & $0$ & $-2$ & $-1$ & $-4$ & $1$ & $0$\\
    $a_2$ & $15$  & $1$ & $0$ & $-3$ & $0$ & $-3$ & $0$ & $1$\\
    $x_2$ & $15$  & $1$ & $1$ & $1$ & $0$ & $1$ & $0$ & $0$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.tableau(solution.bases, two_phase_split=solution.phase1_end)
    assert normalize(rendered) == normalize(expected)

    # NOTE: the example writes the columns in order x, h_1, h_3, a_1, a_2 —
    # same as ours (decision, slacks, artificials).


def test_unbounded_golden(no_acotado_a):
    # examples/dos_fases_no_acotado_a_sol.tex lines 42-61
    solution = two_phase(no_acotado_a.standard())
    assert solution.status is Status.UNBOUNDED
    assert solution.message == MSG_UNBOUNDED
    assert solution.phase1_end == len(solution.bases) == 2
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccccc|}
     & $z$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_2$ & $a_1$\\
    Fase 1 & $20$ & $2$ & $4$ & $-2$ & $-1$ & $0$ & $0$ \\
    Fase 2 & $0$ & $3$ & $2$ & $4$ & $0$ & $0$ & $0$ \\
    \hline
    $a_1$ & $20$  & $2$ & $4$ & $-2$ & $-1$ & $0$ & $1$\\
    $h_2$ & $80$  & $1$ & $1$ & $-1$ & $0$ & $1$ & $0$\\
    \hline
    Fase 1 & $0$ & $0$ & $0$ & $0$ & $0$ & $0$ & $-1$ \\
    Fase 2 & $-10$ & $2$ & $0$ & $5$ & $\frac{1}{2}$ & $0$ & $\frac{-1}{2}$ \\
    \hline
    $x_2$ & $5$  & $\frac{1}{2}$ & $1$ & $\frac{-1}{2}$ & $\frac{-1}{4}$ & $0$ & $\frac{1}{4}$\\
    $h_2$ & $75$  & $\frac{1}{2}$ & $0$ & $\frac{-1}{2}$ & $\frac{1}{4}$ & $1$ & $\frac{-1}{4}$\\
    \hline
    \end{tabular}
    \end{center}
    """
    rendered = latex.tableau(
        solution.bases, two_phase_split=solution.phase1_end, frac=True
    )
    assert normalize(rendered) == normalize(expected)


def test_tableau_can_hide_artificial_columns(dos_fases_a):
    solution = two_phase(dos_fases_a.standard())
    hidden = latex.tableau(
        solution.bases, two_phase_split=solution.phase1_end, include_artificials=False
    )
    header = hidden.splitlines()[2]
    assert "a_1" not in header            # the a_1 column is gone...
    assert "$5/8$" not in hidden          # ...and so is its reduced cost
    assert r"\begin{tabular}{c|c|ccc|}" in hidden  # one column less
    # basic-variable row labels stay, even for a basic artificial:
    assert "$a_1$ & $80$" in hidden
    assert "$x_1$ & $15$" in hidden

    shown = latex.tableau(solution.bases, two_phase_split=solution.phase1_end)
    assert "$a_1$" in shown and "$5/8$" in shown


def test_two_phase_without_artificials_falls_back_to_simplex():
    solution = two_phase(parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6").standard())
    assert solution.status is Status.OPTIMAL
    assert solution.phase1_end is None
    assert solution.z == F(9)


def test_every_phase1_basis_is_feasible(dos_fases_a, no_acotado_a):
    for problem in (dos_fases_a, no_acotado_a):
        solution = two_phase(problem.standard())
        assert all(basis.is_feasible for basis in solution.bases)
