"""Sample exam for course MCIO1/MAD1, academic year 2026-27.

Variants A and B reuse the same problem bank in a different order, which is a
simple way to discourage copying while keeping a single answer key per problem.
"""

from __future__ import annotations

from exams.bank import load_problem
from exams.models import Exam

_VARIANT_ORDER = {
    "A": ["mueblespro", "dieta_min"],
    "B": ["dieta_min", "mueblespro"],
}


def build(variant: str = "A") -> Exam:
    order = _VARIANT_ORDER.get(variant.upper())
    if order is None:
        raise KeyError(f"Unknown variant {variant!r}. Available: {', '.join(_VARIANT_ORDER)}")
    return Exam(
        id="mcio1_mad1_2627",
        title="MCIO1/MAD1 -- Linear Programming",
        course="MCIO1/MAD1",
        year=2026,
        problems=[load_problem(name) for name in order],
        variant=variant.upper(),
    )
