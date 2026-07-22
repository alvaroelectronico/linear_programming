from fractions import Fraction

from linprog import latex, parse_problem

from conftest import normalize

F = Fraction


def test_fmt_default_inline():
    assert latex.fmt(F(3)) == "3"
    assert latex.fmt(F(-3)) == "-3"
    assert latex.fmt(F(7, 2)) == "7/2"
    assert latex.fmt(F(-5, 8)) == "-5/8"


def test_fmt_frac_sign_in_numerator():
    assert latex.fmt(F(7, 2), frac=True) == r"\frac{7}{2}"
    assert latex.fmt(F(-5, 8), frac=True) == r"\frac{-5}{8}"
    assert latex.fmt(F(-3), frac=True) == "-3"


def test_expression_omits_unit_and_zero_coefficients():
    terms = [(F(3), "x_1"), (F(1), "x_2"), (F(0), "x_3"), (F(-1), "h_1"), (F(-7, 2), "a_1")]
    assert latex.expression(terms) == "3x_1 + x_2 - h_1 - 7/2a_1"


def test_problem_tex_matches_statement(no_factible_a):
    # examples/dos_fases_no_factible_a_sol.tex lines 3-12
    expected = r"""
    \begin{equation}
    \begin{split}
    \mbox{max. } z = 3x_1 + 2x_2 + x_3\\
    s.a.:\\
    2x_1 + 4x_2 + 2x_3 \geq 80\\
    4x_1 + 3x_2 = 60\\
    x_1 + x_2 + x_3 \leq 15\\
    x_1,\,x_2,\,x_3\geq 0
    \end{split}
    \end{equation}
    """
    assert normalize(latex.problem_tex(no_factible_a)) == normalize(expected)


def test_standard_form_tex_golden(no_factible_a):
    # examples/dos_fases_no_factible_a_sol.tex lines 18-27 (no artificials)
    expected = r"""
    \begin{equation}
    \begin{split}
    \mbox{max. } z = 3x_1 + 2x_2 + x_3\\
    s.a.:\\
    2x_1 + 4x_2 + 2x_3 - h_1 = 80\\
    4x_1 + 3x_2 = 60\\
    x_1 + x_2 + x_3 + h_3 = 15\\
    x_1,\,x_2,\,x_3,\,h_1,\,h_3\geq 0
    \end{split}
    \end{equation}
    """
    assert normalize(latex.standard_form_tex(no_factible_a.standard())) == normalize(expected)


def test_phase1_tex_golden(no_factible_a):
    # examples/dos_fases_no_factible_a_sol.tex lines 31-40
    expected = r"""
    \begin{equation}
    \begin{split}
    \mbox{max. } z' = -a_1 - a_2\\
    s.a.:\\
    2x_1 + 4x_2 + 2x_3 - h_1 + a_1 = 80\\
    4x_1 + 3x_2 + a_2 = 60\\
    x_1 + x_2 + x_3 + h_3 = 15\\
    x_1,\,x_2,\,x_3,\,h_1,\,h_3,\,a_1,\,a_2\geq 0
    \end{split}
    \end{equation}
    """
    assert normalize(latex.phase1_tex(no_factible_a.standard())) == normalize(expected)


def test_min_standard_form_is_rendered_as_max(lemke_min):
    # examples/lemke_sol.tex lines 46-55: min -> max with negated coefficients
    expected = r"""
    \begin{equation}
    \begin{split}
    \mbox{max. } z = -10x_1 - 20x_2 - 30x_3\\
    s.a.:\\
    4x_1 + 2x_2 + 8x_3 + h_1 = 1000\\
    x_2 + x_3 + h_2 = 500\\
    x_2 + x_3 - h_3 = 500\\
    x_1,\,x_2,\,x_3,\,h_1,\,h_2,\,h_3\geq 0
    \end{split}
    \end{equation}
    """
    assert normalize(latex.standard_form_tex(lemke_min.standard())) == normalize(expected)


def test_canonical_form_splits_equalities():
    problem = parse_problem("max x + y\nx + y = 10\nx - y >= 2")
    expected = r"""
    \begin{equation}
    \begin{split}
    \mbox{max. } z = x + y\\
    s.a.:\\
    x + y \leq 10\\
    -x - y \leq -10\\
    -x + y \leq -2\\
    x,\,y\geq 0
    \end{split}
    \end{equation}
    """
    assert normalize(latex.canonical_form_tex(problem)) == normalize(expected)


def test_canonical_form_min_uses_geq():
    problem = parse_problem("min 2x + y\nx + y <= 8")
    tex = latex.canonical_form_tex(problem)
    assert r"\mbox{min. }" in tex
    assert r"-x - y \geq -8" in tex


def test_elements_tex(dos_fases_a):
    parts = latex.elements_tex(dos_fases_a)
    assert normalize(parts["A"]) == normalize("\\begin{pmatrix}\n4 & 2\\\\\n2 & 3\\\\\n\\end{pmatrix}")
    assert normalize(parts["b"]) == normalize("\\begin{pmatrix}\n80\\\\\n60\\\\\n\\end{pmatrix}")
    assert normalize(parts["c"]) == normalize("\\begin{pmatrix}\n1 & 4\\\\\n\\end{pmatrix}")


def test_frac_toggle_in_formulation():
    problem = parse_problem("max 3/2x + y\nx + y <= 4")
    assert "3/2x" in latex.problem_tex(problem)
    assert r"\frac{3}{2}x" in latex.problem_tex(problem, frac=True)
