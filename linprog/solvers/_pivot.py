"""Row operations on a rational simplex tableau.

The tableau is a list of rows (each a list of ``Fraction``); row 0 holds the
objective/reduced-cost row and the last column holds the right-hand side. These
helpers are pure functions or in-place mutators shared by the Simplex and Lemke
solvers.
"""

from __future__ import annotations

from fractions import Fraction
from warnings import warn

Row = list
Tableau = list


def sum_rows(row1: Row, row2: Row) -> Row:
    """Element-wise sum of two rows."""
    return [a + b for a, b in zip(row1, row2)]


def scale_row(constant: Fraction, row: Row) -> Row:
    """Return ``row`` with every element multiplied by ``constant``."""
    return [constant * value for value in row]


def argmax(row: Row) -> int:
    """Index of the largest element (first one wins on ties)."""
    best = 0
    for i in range(len(row)):
        if row[i] > row[best]:
            best = i
    return best


def argmin(row: Row) -> int:
    """Index of the smallest element (first one wins on ties)."""
    best = 0
    for i in range(len(row)):
        if row[i] < row[best]:
            best = i
    return best


def normalize_pivot_row(tableau: Tableau, key_row: int, pivot: Fraction) -> None:
    """Divide the pivot row by the pivot value, in place."""
    tableau[key_row] = [value / pivot for value in tableau[key_row]]


def clear_pivot_column(tableau: Tableau, key_column: int, key_row: int) -> None:
    """Zero out every entry of the pivot column except the pivot, in place."""
    for i in range(len(tableau)):
        if i == key_row:
            continue
        factor = tableau[i][key_column]
        tableau[i] = [
            value - tableau[key_row][j] * factor
            for j, value in enumerate(tableau[i])
        ]


def min_ratio_row(tableau: Tableau, key_column: int) -> int:
    """Pick the leaving row by the minimum-ratio test.

    Returns ``-1`` when the column has no positive entry (unbounded problem).
    """
    min_val = float("inf")
    min_row = 0
    for i in range(1, len(tableau)):
        if tableau[i][key_column] > 0:
            ratio = tableau[i][-1] / tableau[i][key_column]
            if ratio < min_val:
                min_val = ratio
                min_row = i
    if min_val == float("inf"):
        warn("Unbounded problem")
        return -1
    if min_val == 0:
        warn("Degeneracy")
    return min_row
