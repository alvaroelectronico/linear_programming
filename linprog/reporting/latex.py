"""Render fractions, matrices and expressions as LaTeX strings."""

from __future__ import annotations

from fractions import Fraction

import numpy as np


def fraction_to_tex(frac, use_dollar: bool = False, frac_command: bool = True) -> str:
    """Render a fraction (or float) as LaTeX.

    Args:
        frac: a ``Fraction``, ``float`` or ``numpy.float64``.
        use_dollar: wrap the result in inline-math ``$...$``.
        frac_command: use ``\\frac{a}{b}`` when True, otherwise ``a/b``.
    """
    if isinstance(frac, (float, np.float64)):
        frac = Fraction(float(frac)).limit_denominator()

    if frac.denominator in (0, 1):
        result = f"{frac.numerator:.0f}"
    elif frac_command:
        result = f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
    else:
        result = f"{frac.numerator}/{frac.denominator}"

    return f"${result}$" if use_dollar else result


def element_to_tex(element, frac_command: bool = True) -> str:
    """Render a single matrix element (without a trailing separator)."""
    if isinstance(element, Fraction):
        return fraction_to_tex(element, frac_command=frac_command)
    if int(element) == element:
        return f"{element:.0f}"
    return f"{element}"


def matrix_to_tex(matrix: np.ndarray, brackets: str = "round", frac_command: bool = True) -> str:
    """Render a matrix as a LaTeX ``pmatrix``.

    A 1x1 matrix collapses to its single scalar, matching the textbook
    convention of showing inner products as plain numbers.
    """
    if matrix.shape == (1, 1):
        return fraction_to_tex(matrix[0][0], frac_command=frac_command)

    open_env, close_env = ("\\begin{pmatrix}\n", "\\end{pmatrix}\n")
    tex = open_env
    for r in range(matrix.shape[0]):
        row = [
            element_to_tex(matrix[r, c], frac_command=frac_command)
            for c in range(matrix.shape[1])
        ]
        tex += " & ".join(row) + "\\\\\n"
    tex += close_env
    return tex


def operations_to_tex(items, frac_command: bool = True) -> str:
    """Concatenate a sequence of matrices, numbers and string literals into TeX."""
    tex = ""
    for item in items:
        if isinstance(item, str):
            tex += item
        elif isinstance(item, np.ndarray):
            tex += matrix_to_tex(item, frac_command=frac_command)
        elif isinstance(item, (int, float)):
            tex += str(item)
    return tex


def create_equation(content: str) -> str:
    """Wrap content in an ``equation``/``split`` environment."""
    return "\\begin{equation}\n\\begin{split}\n" + content + "\\end{split}\n\\end{equation}"
