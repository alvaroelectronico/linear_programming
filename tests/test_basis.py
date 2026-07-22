from fractions import Fraction

import pytest

from linprog import Basis, SingularBasisError, latex
from linprog.basis import identity, inverse, mat_mul

from conftest import normalize

F = Fraction


def optimal_basis(dos_fases_a):
    sf = dos_fases_a.standard()  # columns: x_1, x_2, h_2, a_1
    return Basis(sf, [0, 1])  # (x_1, x_2)


def test_inverse_gauss_jordan():
    m = [[F(4), F(2)], [F(2), F(3)]]
    assert inverse(m) == [[F(3, 8), F(-1, 4)], [F(-1, 4), F(1, 2)]]
    # needs a row swap (zero pivot):
    m2 = [[F(0), F(1)], [F(1), F(0)]]
    assert inverse(m2) == [[F(0), F(1)], [F(1), F(0)]]


def test_inverse_singular_raises():
    with pytest.raises(SingularBasisError):
        inverse([[F(1), F(2)], [F(2), F(4)]])


def test_dos_fases_a_optimal_basis_quantities(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 38-109 (basis x_1, x_2)
    basis = optimal_basis(dos_fases_a)
    assert basis.names == ("x_1", "x_2")
    assert basis.B == [[F(4), F(2)], [F(2), F(3)]]
    assert basis.B_inv == [[F(3, 8), F(-1, 4)], [F(-1, 4), F(1, 2)]]
    assert basis.c_B == [F(1), F(4)]
    assert basis.u == [F(15), F(10)]
    assert basis.pi == [F(-5, 8), F(7, 4)]
    # V over (x_1, x_2, h_2, a_1) — final "Fase 2" tableau row
    assert basis.V == [F(0), F(0), F(-7, 4), F(5, 8)]
    assert basis.z == F(55)
    assert basis.values() == {"x_1": F(15), "x_2": F(10), "h_2": F(0), "a_1": F(0)}
    assert basis.is_feasible
    assert not basis.is_degenerate
    assert basis.is_optimal  # a_1's positive V is ignored (artificial)
    assert not basis.has_alternate_optimum


def test_b_binv_is_identity(dos_fases_a, no_factible_a):
    for problem in (dos_fases_a, no_factible_a):
        sf = problem.standard()
        basis = Basis(sf, sf.initial_basis())
        assert mat_mul(basis.B, basis.B_inv) == identity(sf.n_rows)


def test_initial_basis_of_two_phase_problem(dos_fases_a):
    sf = dos_fases_a.standard()
    basis = Basis(sf, sf.initial_basis())  # (a_1, h_2)
    assert basis.names == ("a_1", "h_2")
    assert basis.u == [F(80), F(60)]
    # phase-1 reduced costs: initial "Fase 1" tableau row of the example
    assert basis.reduced_costs(sf.phase1_c()) == [F(4), F(2), F(0), F(0)]
    assert basis.objective_value(sf.phase1_c()) == F(-80)
    # phase-2 row: V = c at the identity basis
    assert basis.V == [F(1), F(4), F(0), F(0)]
    assert basis.z == F(0)


def test_infeasible_and_degenerate_flags(dos_fases_a):
    sf = dos_fases_a.standard()
    infeasible = Basis(sf, [1, 2])  # x_2, h_2: u = (40, -60) -> infeasible
    assert infeasible.u == [F(40), F(-60)]
    assert not infeasible.is_feasible
    assert not infeasible.is_optimal


def test_wrong_basis_size_raises(dos_fases_a):
    with pytest.raises(ValueError):
        Basis(dos_fases_a.standard(), [0])


def test_basis_matrix_tex(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 40-56
    basis = optimal_basis(dos_fases_a)
    expected_B = r"""
    \begin{equation}
    \begin{split}
    B =\begin{pmatrix}
    4 & 2\\
    2 & 3\\
    \end{pmatrix}
    \end{split}
    \end{equation}
    """
    expected_B_inv = r"""
    \begin{equation}
    \begin{split}
    B^{-1} =\begin{pmatrix}
    \frac{3}{8} & \frac{-1}{4}\\
    \frac{-1}{4} & \frac{1}{2}\\
    \end{pmatrix}
    \end{split}
    \end{equation}
    """
    assert normalize(latex.basis_matrix_tex(basis)) == normalize(expected_B)
    assert normalize(latex.basis_inverse_tex(basis, frac=True)) == normalize(expected_B_inv)


def test_shadow_prices_and_reduced_costs_tex(dos_fases_a):
    basis = optimal_basis(dos_fases_a)
    pi = latex.shadow_prices_tex(basis)
    assert "\\pi^B =" in pi and "-5/8 & 7/4" in pi
    v = latex.reduced_costs_tex(basis)
    assert "V^B =" in v and "0 & 0 & -7/4" in v
    assert "5/8" not in v  # artificial column hidden by default
    v_all = latex.reduced_costs_tex(basis, include_artificials=True)
    assert "5/8" in v_all


def test_objective_value_tex(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 99-109
    basis = optimal_basis(dos_fases_a)
    expected = r"""
    \begin{equation}
    \begin{split}
    z^B=c^Bu^B = \begin{pmatrix}
    1 & 4\\
    \end{pmatrix}
    \begin{pmatrix}
    15\\
    10\\
    \end{pmatrix}
     = 55
    \end{split}
    \end{equation}
    """
    assert normalize(latex.objective_value_tex(basis)) == normalize(expected)
