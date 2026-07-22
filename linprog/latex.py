"""All LaTeX rendering.

Every function returns a LaTeX *fragment* (Spanish exam material) meant to be
pasted or ``\\input`` into a document.  Data classes hold no rendering logic:
these functions take ``Problem`` / ``StandardForm`` objects (and, in later
phases, ``Basis``) as arguments.

Every rendering function accepts a keyword-only ``frac`` flag: ``False`` (the
default) renders fractions inline (``-5/2``); ``True`` renders ``\\frac{-5}{2}``
with the minus sign in the numerator.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .problem import Problem, Sense, StandardForm

# --- Spanish wording, kept together so it can be audited at a glance --------

HDR_PHASE1 = r"\textbf{Formulación de la primera fase}"
HDR_PHASE2 = r"\textbf{Formulación de la segunda fase}"
HDR_TWO_PHASE = r"\textbf{Resolución mediante el método de las dos fases}"
HDR_OPTIMAL_BASIS = r"\textbf{Base óptima y su inversa}"
HDR_MULTIPLIERS = r"\textbf{Multiplicadores del símplex y costes reducidos}"
HDR_OBJECTIVE_VALUE = r"\textbf{Valor de la función objetivo}"
LBL_OPTIMAL_SOLUTION = r"\textbf{Solución óptima:}"
LBL_PHASE1 = "Fase 1"
LBL_PHASE2 = "Fase 2"
SUBJECT_TO = r"s.a.:"

_SENSE_TEX: dict[Sense, str] = {"<=": r"\leq", ">=": r"\geq", "=": "="}
_GOAL_TEX = {"max": r"\mbox{max. }", "min": r"\mbox{min. }"}


# --- numbers and expressions -------------------------------------------------


def fmt(x: Fraction | int, *, frac: bool = False) -> str:
    """Render an exact number: ``3``, ``-5/2`` or (with ``frac=True``)
    ``\\frac{-5}{2}`` — the sign always goes in the numerator."""
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    if frac:
        return rf"\frac{{{x.numerator}}}{{{x.denominator}}}"
    return f"{x.numerator}/{x.denominator}"


def _term(coef: Fraction, name: str, *, first: bool, frac: bool) -> str:
    """One monomial with its leading sign; coefficient 1 is left implicit."""
    sign = "-" if coef < 0 else ("" if first else "+")
    magnitude = abs(coef)
    coef_tex = "" if magnitude == 1 else fmt(magnitude, frac=frac)
    separator = "" if first else " "
    prefix = f"{separator}{sign}" if first else f"{separator}{sign} "
    return f"{prefix}{coef_tex}{name}"


def expression(terms: Sequence[tuple[Fraction, str]], *, frac: bool = False) -> str:
    """A linear expression like ``3x_1 + 2x_2 - h_1`` (zero terms skipped)."""
    parts: list[str] = []
    for coef, name in terms:
        if coef == 0:
            continue
        parts.append(_term(coef, name, first=not parts, frac=frac))
    return "".join(parts) if parts else "0"


def pmatrix(rows: Sequence[Sequence], *, frac: bool = False) -> str:
    """Cells may be numbers or ready-made LaTeX strings (e.g. a symbolic b_3)."""
    body = "".join(
        " & ".join(x if isinstance(x, str) else fmt(x, frac=frac) for x in row)
        + "\\\\\n"
        for row in rows
    )
    return "\\begin{pmatrix}\n" + body + "\\end{pmatrix}"


def _equation(lines: Sequence[str]) -> str:
    body = "\\\\\n".join(lines)
    return f"\\begin{{equation}}\n\\begin{{split}}\n{body}\n\\end{{split}}\n\\end{{equation}}"


def _nonnegativity(names: Sequence[str]) -> str:
    return ",\\,".join(names) + r"\geq 0"


def _formulation(
    goal: str,
    z_name: str,
    objective: Sequence[tuple[Fraction, str]],
    constraint_lines: Sequence[str],
    var_names: Sequence[str],
    *,
    frac: bool,
) -> str:
    lines = [
        f"{_GOAL_TEX[goal]} {z_name} = {expression(objective, frac=frac)}",
        SUBJECT_TO,
        *constraint_lines,
        _nonnegativity(var_names),
    ]
    return _equation(lines)


# --- problem formulations ----------------------------------------------------


def _terms(coeffs: dict[str, Fraction]) -> list[tuple[Fraction, str]]:
    return [(coef, name) for name, coef in coeffs.items()]


def problem_tex(problem: Problem, *, frac: bool = False) -> str:
    """The problem exactly as stated by the user."""
    constraint_lines = [
        f"{expression(_terms(k.coeffs), frac=frac)} "
        f"{_SENSE_TEX[k.sense]} {fmt(k.rhs, frac=frac)}"
        for k in problem.constraints
    ]
    return _formulation(
        problem.goal, "z", _terms(problem.objective),
        constraint_lines, problem.variables, frac=frac,
    )


def canonical_form_tex(problem: Problem, *, frac: bool = False) -> str:
    """Canonical form: every constraint as ``<=`` for a max problem (``>=``
    for a min problem); each ``=`` becomes a pair of opposite inequalities."""
    target: Sense = "<=" if problem.goal == "max" else ">="
    constraint_lines: list[str] = []
    for constraint in problem.constraints:
        versions: list[tuple[dict[str, Fraction], Fraction]] = []
        if constraint.sense in (target, "="):
            versions.append((constraint.coeffs, constraint.rhs))
        if constraint.sense != target:  # flip (also the '=' twin)
            versions.append(
                ({v: -x for v, x in constraint.coeffs.items()}, -constraint.rhs)
            )
        for coeffs, rhs in versions:
            constraint_lines.append(
                f"{expression(_terms(coeffs), frac=frac)} "
                f"{_SENSE_TEX[target]} {fmt(rhs, frac=frac)}"
            )
    return _formulation(
        problem.goal, "z", _terms(problem.objective),
        constraint_lines, problem.variables, frac=frac,
    )


def _standard_rows(sf: StandardForm, *, with_artificials: bool, frac: bool) -> list[str]:
    n_cols = sf.n_cols if with_artificials else sf.n_cols - sf.n_artificials
    return [
        f"{expression([(row[j], sf.variables[j]) for j in range(n_cols)], frac=frac)}"
        f" = {fmt(sf.b[i], frac=frac)}"
        for i, row in enumerate(sf.A)
    ]


def standard_form_tex(sf: StandardForm, *, frac: bool = False) -> str:
    """Standard form: max objective, equality rows with slacks, x >= 0.
    Artificial variables belong to the two-phase method, not to the standard
    form, so they are not shown here."""
    names = sf.variables[: sf.n_cols - sf.n_artificials]
    objective = [(sf.c[j], names[j]) for j in range(len(names))]
    return _formulation(
        "max", "z", objective,
        _standard_rows(sf, with_artificials=False, frac=frac), names, frac=frac,
    )


def phase1_tex(sf: StandardForm, *, frac: bool = False) -> str:
    """First-phase problem: max z' = -sum of artificials, over the standard
    rows extended with the artificial columns."""
    c1 = sf.phase1_c()
    objective = [(c1[j], sf.variables[j]) for j in range(sf.n_cols)]
    return _formulation(
        "max", "z'", objective,
        _standard_rows(sf, with_artificials=True, frac=frac), sf.variables, frac=frac,
    )


def phase2_tex(sf: StandardForm, *, frac: bool = False) -> str:
    """Second-phase problem: the original (max-form) objective over the
    standard rows, once the artificials are gone."""
    return standard_form_tex(sf, frac=frac)


# --- the simplex tableau -----------------------------------------------------


def _tableau_row(label: str, value: Fraction, cells: Sequence[Fraction], *, frac: bool) -> str:
    numbers = " & ".join(f"${fmt(x, frac=frac)}$" for x in [value, *cells])
    return f"{label} & {numbers}\\\\"


def tableau(
    bases: Sequence,
    *,
    two_phase_split: int | None = None,
    include_artificials: bool = True,
    frac: bool = False,
    value_label: str = "z",
) -> str:
    """The exam tableau for any sequence of bases (all the bases a solver
    visited, or any subset), stacked and separated by ``\\hline``.

    Layout (see examples/dos_fases_a_sol.tex): column 1 is the basic-variable
    label (empty or ``Fase 1``/``Fase 2`` on objective rows), column 2 — headed
    ``$z$`` — is the value column, then one column per variable.  Objective
    rows show ``-z^B`` in the value column and the reduced costs ``V^B_j`` in
    the variable cells; body rows show ``u_i`` and ``B^{-1}A``.

    ``two_phase_split``: number of leading bases that belong to phase 1; those
    blocks carry two objective rows (``Fase 1`` and ``Fase 2``), later blocks
    only the ``Fase 2`` row.  ``None`` renders a single unlabeled objective row.

    ``include_artificials=False`` hides the artificial-variable columns (their
    rows and labels stay — only the columns are dropped).
    """
    sf = bases[0].sf
    n_shown = sf.n_cols if include_artificials else sf.n_cols - sf.n_artificials
    lines = [
        r"\begin{center}",
        r"\begin{tabular}{" + "c|c|" + "c" * n_shown + "|}",
        " & ".join(
            [" ", f"${value_label}$", *(f"${v}$" for v in sf.variables[:n_shown])]
        ) + r"\\",
    ]
    for k, basis in enumerate(bases):
        if two_phase_split is None:
            lines.append(_tableau_row("", -basis.z, basis.V[:n_shown], frac=frac))
        else:
            if k < two_phase_split:
                c1 = sf.phase1_c()
                lines.append(_tableau_row(
                    LBL_PHASE1, -basis.objective_value(c1),
                    basis.reduced_costs(c1)[:n_shown], frac=frac,
                ))
            lines.append(_tableau_row(LBL_PHASE2, -basis.z, basis.V[:n_shown], frac=frac))
        lines.append(r"\hline")
        for i, name in enumerate(basis.names):
            lines.append(_tableau_row(
                f"${name}$", basis.u[i], basis.B_inv_A[i][:n_shown], frac=frac,
            ))
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{center}"]
    return "\n".join(lines)


# --- per-basis quantities ----------------------------------------------------


def basis_matrix_tex(basis, *, frac: bool = False) -> str:
    """``B = (...)`` as an equation."""
    return _equation([f"B ={pmatrix(basis.B, frac=frac)}"])


def basis_inverse_tex(basis, *, frac: bool = False) -> str:
    """``B^{-1} = (...)`` as an equation."""
    return _equation([f"B^{{-1}} ={pmatrix(basis.B_inv, frac=frac)}"])


def shadow_prices_tex(basis, *, verbose: bool = False, frac: bool = False) -> str:
    """``pi^B`` as an equation.  With ``verbose``, the generic formula and the
    full matrix product are spelled out: ``pi^B = c^B B^{-1} = (...)(...) = (...)``."""
    result = pmatrix([basis.pi], frac=frac)
    if not verbose:
        return _equation([f"\\pi^B ={result}"])
    chain = (
        f"\\pi^B = c^BB^{{-1}} = {pmatrix([basis.c_B], frac=frac)}\n"
        f"{pmatrix(basis.B_inv, frac=frac)}\n"
        f" = {result}"
    )
    return _equation([chain])


def reduced_costs_tex(
    basis, *, verbose: bool = False, include_artificials: bool = False,
    frac: bool = False,
) -> str:
    """``V^B`` as an equation (artificial columns hidden by default, as in the
    exams).  With ``verbose``, the generic formula and every factor are spelled
    out: ``V^B = c - c^B B^{-1} A = (...) - (...)(...)(...) = (...)``."""
    sf = basis.sf
    n_cols = sf.n_cols if include_artificials else sf.n_cols - sf.n_artificials
    result = pmatrix([basis.V[:n_cols]], frac=frac)
    if not verbose:
        return _equation([f"V^B ={result}"])
    chain = (
        f"V^B = c-c^BB^{{-1}}A = {pmatrix([sf.c[:n_cols]], frac=frac)}\n"
        f" - {pmatrix([basis.c_B], frac=frac)}\n"
        f"{pmatrix(basis.B_inv, frac=frac)}\n"
        f"{pmatrix([row[:n_cols] for row in sf.A], frac=frac)}\n"
        f" = {result}"
    )
    return _equation([chain])


def objective_value_tex(basis, *, frac: bool = False) -> str:
    """``z^B = c^B u^B = (...)(...) = value`` as an equation."""
    chain = (
        f"z^B=c^Bu^B = {pmatrix([basis.c_B], frac=frac)}\n"
        f"{pmatrix([[x] for x in basis.u], frac=frac)}\n"
        f" = {fmt(basis.z, frac=frac)}"
    )
    return _equation([chain])


def elements_tex(problem: Problem, *, frac: bool = False) -> dict[str, str]:
    """The problem's building blocks as LaTeX: A, b (column) and c (row)."""
    return {
        "A": pmatrix(problem.A, frac=frac),
        "b": pmatrix([[x] for x in problem.b], frac=frac),
        "c": pmatrix([problem.c], frac=frac),
    }
