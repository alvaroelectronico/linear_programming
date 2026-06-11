"""LaTeX rendering of linear-programming objects."""

from linprog.reporting.document import (
    DEFAULT_PREAMBLE_PACKAGES,
    latex_document,
    render_worked_solution,
)
from linprog.reporting.latex import (
    create_equation,
    element_to_tex,
    fraction_to_tex,
    matrix_to_tex,
    operations_to_tex,
)

__all__ = [
    "create_equation",
    "element_to_tex",
    "fraction_to_tex",
    "matrix_to_tex",
    "operations_to_tex",
    "latex_document",
    "render_worked_solution",
    "DEFAULT_PREAMBLE_PACKAGES",
]
