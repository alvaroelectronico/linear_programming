"""Assemble LaTeX fragments into worked solutions and standalone documents.

The rest of the package returns LaTeX *fragments* (equation/tabular
environments). These two helpers are the only place that builds a complete,
compilable document, and a full worked solution from a solved
:class:`~linprog.problem.LinearProgram`. They reuse the existing fragment
methods and reimplement no LaTeX.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid a circular import; only needed for type hints
    from linprog.problem import LinearProgram

DEFAULT_PREAMBLE_PACKAGES = ("amsmath", "amssymb", "geometry")


def latex_document(
    body: str,
    *,
    title: str | None = None,
    author: str | None = None,
    documentclass: str = "article",
    packages: tuple[str, ...] = DEFAULT_PREAMBLE_PACKAGES,
    geometry: str = "margin=2.5cm",
    extra_preamble: str = "",
) -> str:
    """Wrap a LaTeX ``body`` fragment in a complete, compilable document.

    Pure string builder -- writes nothing. ``geometry`` is the option string
    passed to the ``geometry`` package; ``extra_preamble`` is inserted verbatim
    just before ``\\begin{document}``.
    """
    lines = [f"\\documentclass{{{documentclass}}}"]
    for package in packages:
        if package == "geometry" and geometry:
            lines.append(f"\\usepackage[{geometry}]{{geometry}}")
        else:
            lines.append(f"\\usepackage{{{package}}}")
    if title is not None:
        lines.append(f"\\title{{{title}}}")
    if author is not None:
        lines.append(f"\\author{{{author}}}")
    if extra_preamble:
        lines.append(extra_preamble)
    lines.append("\\begin{document}")
    if title is not None:
        lines.append("\\maketitle")
    lines.append(body)
    lines.append("\\end{document}")
    return "\n".join(lines) + "\n"


def render_worked_solution(
    problem: LinearProgram,
    *,
    include_formulation: bool = True,
    include_phase1: bool = True,
    include_tableau: bool = True,
    include_basis_details: bool = False,
    with_artificials: bool = True,
    frac_command: bool = True,
    section_headers: bool = True,
) -> str:
    """Assemble the worked-solution *body* (a fragment, not a document).

    Composes the existing fragment methods: the formulation, the phase-1
    formulation, the full tableau and, optionally, the per-basis quantities
    (``B``, ``B^{-1}``, ``\\pi^B``, ``u^B``, ``v^B``). When the problem is
    infeasible or unbounded there is no optimal basis, so a short note is
    emitted and the tableau/basis sections are skipped.
    """

    def header(text: str) -> str:
        return f"\\section*{{{text}}}\n" if section_headers else ""

    parts: list[str] = []

    if include_formulation:
        parts.append(header("Formulación"))
        parts.append(problem.formulation_tex())

    result = problem.result
    if getattr(result, "is_infeasible", False):
        parts.append(header("Resultado"))
        parts.append("\\textbf{El problema es infactible.}")
        return "\n\n".join(parts) + "\n"
    if getattr(result, "is_unbounded", False):
        parts.append(header("Resultado"))
        parts.append("\\textbf{El problema es no acotado.}")
        return "\n\n".join(parts) + "\n"

    if include_phase1 and problem.standard_form.num_artificial_vars > 0:
        parts.append(header("Formulación de la primera fase"))
        parts.append(problem.formulation_phase1_tex())

    if include_tableau:
        parts.append(header("Resolución"))
        parts.append(
            problem.compose_tableau(
                problem.basic_solutions,
                with_artificials=with_artificials,
                frac_command=frac_command,
            )
        )

    if include_basis_details:
        parts.append(header("Detalles de la base"))
        for i, basic_solution in enumerate(problem.basic_solutions, start=1):
            parts.append(f"\\subsection*{{Base {i}}}" if section_headers else "")
            parts.append(basic_solution.B_tex(frac_command=frac_command))
            parts.append(basic_solution.invB_tex(frac_command=frac_command))
            parts.append(basic_solution.piB_tex(frac_command=frac_command))
            parts.append(basic_solution.uB_tex(frac_command=frac_command))
            parts.append(basic_solution.vB_tex(frac_command=frac_command))

    return "\n\n".join(part for part in parts if part) + "\n"
