from linprog import latex, parse_problem, simplex

from conftest import normalize


def production_solution():
    problem = parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6")
    return simplex(problem.standard())


def test_full_tableau_golden():
    # Hand-computed, in the CLAUDE.md format: one block per visited basis,
    # objective row (value = -z, cells = V) above the basic-variable rows.
    solution = production_solution()
    expected = r"""
    \begin{center}
    \begin{tabular}{c|c|cccc|}
     & $z$ & $x$ & $y$ & $h_1$ & $h_2$\\
     & $0$ & $2$ & $3$ & $0$ & $0$\\
    \hline
    $h_1$ & $4$ & $1$ & $1$ & $1$ & $0$\\
    $h_2$ & $6$ & $1$ & $3$ & $0$ & $1$\\
    \hline
     & $-6$ & $1$ & $0$ & $0$ & $-1$\\
    \hline
    $h_1$ & $2$ & $2/3$ & $0$ & $1$ & $-1/3$\\
    $y$ & $2$ & $1/3$ & $1$ & $0$ & $1/3$\\
    \hline
     & $-9$ & $0$ & $0$ & $-3/2$ & $-1/2$\\
    \hline
    $x$ & $3$ & $1$ & $0$ & $3/2$ & $-1/2$\\
    $y$ & $1$ & $0$ & $1$ & $-1/2$ & $1/2$\\
    \hline
    \end{tabular}
    \end{center}
    """
    assert normalize(latex.tableau(solution.bases)) == normalize(expected)


def test_tableau_accepts_any_subset_of_bases():
    solution = production_solution()
    only_last = latex.tableau([solution.final])
    assert normalize(only_last).count(r"\hline") == 2  # one block
    assert "$-9$" in only_last
    only_first = latex.tableau(solution.bases[:1])
    assert "$-9$" not in only_first
    assert "$0$ & $2$ & $3$" in only_first


def test_tableau_frac_toggle():
    solution = production_solution()
    assert "$2/3$" in latex.tableau(solution.bases)
    assert r"$\frac{2}{3}$" in latex.tableau(solution.bases, frac=True)


def test_tableau_value_label():
    # lemke_sol.tex heads the value column with $s$ instead of $z$
    solution = production_solution()
    assert " & $s$ & $x$" in latex.tableau(solution.bases, value_label="s")
