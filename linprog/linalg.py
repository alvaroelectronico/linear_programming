"""Exact matrix operations for rational (``Fraction``) matrices.

These routines deliberately avoid floating-point linear algebra so that the
tableaux shown to students stay exact. They are written for the small matrices
that arise in textbook problems, not for performance.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from linprog.fractions_utils import array_to_fraction


def determinant(matrix: np.ndarray) -> Fraction:
    """Compute the determinant by Laplace (cofactor) expansion."""
    size = len(matrix)
    if size == 1:
        return matrix[0][0]
    if size == 2:
        return matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0]

    det = Fraction(0)
    for col in range(size):
        det += matrix[0, col] * cofactor(matrix, 0, col)
    return det


def cofactor(matrix: np.ndarray, row: int, col: int) -> Fraction:
    """Return the (``row``, ``col``) cofactor of ``matrix``."""
    minor = np.delete(np.delete(matrix, row, axis=0), col, axis=1)
    sign = (-1) ** (row + col)
    return sign * determinant(minor)


def inverse(matrix: np.ndarray) -> np.ndarray:
    """Invert a square matrix via the adjugate method, returning Fractions.

    Raises:
        ValueError: if the matrix is not square or is singular.
    """
    matrix = np.array(matrix)
    rows, cols = matrix.shape
    if rows != cols:
        raise ValueError("Matrix must be square")

    det = determinant(matrix)
    if det == 0:
        raise ValueError("Matrix is singular (determinant = 0)")

    # adjugate[j, i] = cofactor(i, j) transposes the cofactor matrix in place.
    adjugate = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            minor = np.delete(np.delete(matrix, i, 0), j, 1)
            adjugate[j, i] = determinant(minor) * (-1) ** (i + j)

    adjugate = array_to_fraction(adjugate)
    det = Fraction(det).limit_denominator()
    return np.array(
        [[adjugate[i, j] / det for j in range(cols)] for i in range(rows)]
    )
