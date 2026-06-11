"""Sample exam for course MCIO1/MAD1, academic year 2026-27.

``items`` are fragment base names in ``ejercicios/``: generated problems (their
``id``) or hand-written ones (the ``.tex`` base name). Variants reorder the same
items. Make sure every listed fragment exists (generate the demo ones first with
``lp-exams render <name>``).
"""

from __future__ import annotations

from exams.models import Exam

_VARIANT_ORDER = {
    "A": ["demo_muebles", "dos_fases_a", "demo_dieta"],
    "B": ["demo_dieta", "dos_fases_b", "demo_muebles"],
}


def build(variant: str = "A") -> Exam:
    order = _VARIANT_ORDER.get(variant.upper())
    if order is None:
        raise KeyError(f"Unknown variant {variant!r}. Available: {', '.join(_VARIANT_ORDER)}")
    return Exam(
        id="mcio1_mad1_2627",
        title="MCIO1/MAD1 -- Programación Lineal",
        course="MCIO1/MAD1",
        year=2026,
        items=order,
        variant=variant.upper(),
    )
