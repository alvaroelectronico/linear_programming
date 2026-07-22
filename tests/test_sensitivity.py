from fractions import Fraction

import pytest

from linprog import Basis, parse_problem, simplex, sensitivity

from conftest import normalize

F = Fraction


@pytest.fixture
def empresa_minera():
    # Reconstructed from examples/empresa_minera_a_sol.tex (its B^{-1}, shadow
    # prices and tableau all match). Optimal basis: (x_4, x_2, x_3).
    return parse_problem(
        """
        max 250x_1 + 300x_2 + 400x_3 + 100x_4
        5x_1 + 3x_2 + 5x_3 + x_4 <= 100
        x_1 + 5x_2 + 3x_3 = 80
        x_2 + x_3 >= 20
        """
    )


def minera_basis(problem):
    sf = problem.standard()  # columns: x_1..x_4, h_1, h_3, a_2, a_3
    basis = Basis(sf, [3, 1, 2])  # (x_4, x_2, x_3)
    # cross-check the reconstruction against the exam:
    assert basis.B_inv == [
        [F(1), F(1), F(-8)],
        [F(0), F(1, 2), F(-3, 2)],
        [F(0), F(-1, 2), F(5, 2)],
    ]
    assert basis.pi == [F(100), F(50), F(-250)]
    assert basis.z == F(9000)
    return basis


def test_rhs_range_golden_interval(empresa_minera):
    # examples/empresa_minera_a_sol.tex line 70: 16 <= b_3 <= 45/2
    interval = sensitivity.rhs_range(minera_basis(empresa_minera), 2)
    assert interval == sensitivity.Interval(F(16), F(45, 2))
    assert F(20) in interval and F(50) not in interval


def test_rhs_range_tex_golden(empresa_minera):
    # examples/empresa_minera_a_sol.tex lines 50-72 (minus the hand-added
    # "< 80/3" aside, which just shows the discarded bound)
    expected = r"""
    \begin{equation}
    \begin{split}
    u^B = B^{-1}b =
    \begin{pmatrix}
    1 & 1 & -8\\
    0 & \frac{1}{2} & \frac{-3}{2}\\
    0 & \frac{-1}{2} & \frac{5}{2}\\
    \end{pmatrix}
    \begin{pmatrix}
    100\\
    80\\
    b_3\\
    \end{pmatrix}
    \geq 0 \Rightarrow
    \begin{pmatrix}
    180 - 8b_3\\
    \frac{80 - 3b_3}{2}\\
    \frac{-80 + 5b_3}{2}\\
    \end{pmatrix}
    \geq 0 \Rightarrow
    16 \leq b_3 \leq \frac{45}{2}
    \end{split}
    \end{equation}
    """
    rendered = sensitivity.rhs_range_tex(minera_basis(empresa_minera), 2, frac=True)
    assert normalize(rendered) == normalize(expected)


def test_rhs_range_one_sided_zumos():
    # examples/zumos_sol.tex lines 116-130: b_1 >= 400, no upper bound
    problem = parse_problem(
        """
        max 3x_1 + 3x_2 + 3x_3 + 3x_4
        2x_1 + 3x_2 + 4x_3 + 2x_4 <= 800
        x_1 + x_2 + x_3 = 200
        """
    )
    basis = Basis(problem.standard(), [3, 0])  # (x_4, x_1)
    assert basis.B_inv == [[F(1, 2), F(-1)], [F(0), F(1)]]
    interval = sensitivity.rhs_range(basis, 0)
    assert interval == sensitivity.Interval(F(400), None)
    tex = sensitivity.rhs_range_tex(basis, 0)
    assert r"b_1 \geq 400" in tex


def test_cost_range_of_a_basic_variable():
    # production problem, optimal basis (x, y): hand-computed c_x in [1, 3]
    solution = simplex(parse_problem("max 2x + 3y\nx + y <= 4\nx + 3y <= 6").standard())
    basis = solution.final
    interval = sensitivity.cost_range(basis, 0)
    assert interval == sensitivity.Interval(F(1), F(3))
    tex = sensitivity.cost_range_tex(basis, 0)
    assert r"1 \leq c_{x} \leq 3" in tex
    assert r"V^B_{h_1}" in tex and r"V^B_{h_2}" in tex


def test_cost_range_of_a_nonbasic_variable():
    # add a variable w with V_w < 0: it stays non-basic while c_w <= pi.A_w
    problem = parse_problem("max 2x + 3y + w\nx + y + w <= 4\nx + 3y + 2w <= 6")
    basis = simplex(problem.standard()).final
    assert basis.names == ("x", "y")
    interval = sensitivity.cost_range(basis, 2)
    assert interval == sensitivity.Interval(None, F(5, 2))
    tex = sensitivity.cost_range_tex(basis, 2)
    assert r"c_{w} \leq 5/2" in tex
    assert r"\pi^B A_{w}" in tex


def test_cost_range_rejects_artificials(dos_fases_a):
    sf = dos_fases_a.standard()
    with pytest.raises(ValueError, match="[Aa]rtificial"):
        sensitivity.cost_range(Basis(sf, [0, 1]), 3)  # a_1's column


def test_affine_tex_styles():
    assert sensitivity.affine_tex((F(180), F(-8)), "b_3") == "180 - 8b_3"
    assert sensitivity.affine_tex((F(40), F(-3, 2)), "b_3") == "(80 - 3b_3)/2"
    assert (
        sensitivity.affine_tex((F(40), F(-3, 2)), "b_3", frac=True)
        == r"\frac{80 - 3b_3}{2}"
    )
    assert sensitivity.affine_tex((F(0), F(1)), "t") == "t"
    assert sensitivity.affine_tex((F(0), F(-1)), "t") == "-t"
    assert sensitivity.affine_tex((F(5), F(0)), "t") == "5"


def test_interval_contains():
    two_sided = sensitivity.Interval(F(1), F(3))
    assert F(1) in two_sided and F(3) in two_sided and F(4) not in two_sided
    free = sensitivity.Interval(None, None)
    assert F(-1000) in free
