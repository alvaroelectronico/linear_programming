"""Helpers for converting numeric arrays to exact rational arithmetic."""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable

import numpy as np


def array_to_fraction(arr: np.ndarray) -> np.ndarray:
    """Return a copy of ``arr`` with every element converted to a ``Fraction``.

    Floats are passed through ``Fraction.limit_denominator`` so that values such
    as ``0.333...`` collapse back to ``1/3`` instead of an unwieldy rational.
    """
    to_fraction = np.vectorize(lambda value: Fraction(value).limit_denominator())
    return to_fraction(arr)


def arrays_to_fraction(arrays: Iterable[np.ndarray]) -> list[np.ndarray]:
    """Apply :func:`array_to_fraction` to each array in ``arrays``."""
    return [array_to_fraction(arr) for arr in arrays]
