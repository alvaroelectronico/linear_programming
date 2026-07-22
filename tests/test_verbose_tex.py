from linprog import Basis, latex

from conftest import normalize


def optimal_basis(dos_fases_a):
    return Basis(dos_fases_a.standard(), [0, 1])  # (x_1, x_2)


def test_verbose_shadow_prices_golden(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 60-73
    expected = r"""
    \begin{equation}
    \begin{split}
    \pi^B = c^BB^{-1} = \begin{pmatrix}
    1 & 4\\
    \end{pmatrix}
    \begin{pmatrix}
    \frac{3}{8} & \frac{-1}{4}\\
    \frac{-1}{4} & \frac{1}{2}\\
    \end{pmatrix}
     = \begin{pmatrix}
    \frac{-5}{8} & \frac{7}{4}\\
    \end{pmatrix}
    \end{split}
    \end{equation}
    """
    rendered = latex.shadow_prices_tex(optimal_basis(dos_fases_a), verbose=True, frac=True)
    assert normalize(rendered) == normalize(expected)


def test_verbose_reduced_costs_golden(dos_fases_a):
    # examples/dos_fases_a_sol.tex lines 75-95 (artificial column excluded)
    expected = r"""
    \begin{equation}
    \begin{split}
    V^B = c-c^BB^{-1}A = \begin{pmatrix}
    1 & 4 & 0\\
    \end{pmatrix}
     - \begin{pmatrix}
    1 & 4\\
    \end{pmatrix}
    \begin{pmatrix}
    \frac{3}{8} & \frac{-1}{4}\\
    \frac{-1}{4} & \frac{1}{2}\\
    \end{pmatrix}
    \begin{pmatrix}
    4 & 2 & 0\\
    2 & 3 & 1\\
    \end{pmatrix}
     = \begin{pmatrix}
    0 & 0 & \frac{-7}{4}\\
    \end{pmatrix}
    \end{split}
    \end{equation}
    """
    rendered = latex.reduced_costs_tex(optimal_basis(dos_fases_a), verbose=True, frac=True)
    assert normalize(rendered) == normalize(expected)


def test_verbose_and_plain_agree_on_the_result(dos_fases_a):
    basis = optimal_basis(dos_fases_a)
    for verbose in (False, True):
        assert "-5/8 & 7/4" in latex.shadow_prices_tex(basis, verbose=verbose)
        assert "0 & 0 & -7/4" in latex.reduced_costs_tex(basis, verbose=verbose)
