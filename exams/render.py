"""Render problem fragments and assemble collection/exam master documents.

A *fragment* is a piece of LaTeX without a preamble (the same shape as the
hand-written problems in ``ejercicios/``). A *master* is a full document that
``\\input``s those fragments under a preamble (header). Generated problems write
``<id>.tex`` (statement) and ``<id>_sol.tex`` (solution) into ``ejercicios/``;
the masters then include any fragment by base name.
"""

from __future__ import annotations

from pathlib import Path

from linprog.reporting import render_worked_solution

from exams.models import Exam, ExamProblem

PAGE_BREAK = "\\clearpage"
TEMPLATES_DIR = Path(__file__).parent / "templates"


# --- fragments ------------------------------------------------------------


def statement_fragment(problem: ExamProblem) -> str:
    """Statement fragment: narrative, optional formulation, optional questions."""
    parts = [problem.statement.strip()]

    if problem.include_formulation:
        formulation = problem.build_program().formulation_tex()
        if problem.statement_label:
            formulation = formulation.replace(
                "\\begin{split}\n",
                f"\\begin{{split}}\n\\label{{{problem.statement_label}}}\n",
                1,
            )
        parts.append(formulation)

    if problem.questions:
        items = "\n".join(f"    \\item {q}" for q in problem.questions)
        parts.append("\\begin{enumerate}\n" + items + "\n\\end{enumerate}")

    return "\n\n".join(parts) + "\n"


def solution_fragment(problem: ExamProblem, *, frac_command: bool = True) -> str:
    """Worked-solution fragment (no preamble, no repeated formulation)."""
    program = problem.build_program()
    return render_worked_solution(
        program,
        include_formulation=False,
        include_phase1=problem.include_phase1,
        include_tableau=problem.include_tableau,
        include_basis_details=problem.include_basis_details,
        frac_command=frac_command,
        section_headers=False,
    )


def write_problem_fragments(
    problem: ExamProblem, ejercicios_dir: Path, *, frac_command: bool = True
) -> tuple[Path, Path]:
    """Write ``<id>.tex`` and ``<id>_sol.tex`` into ``ejercicios_dir``."""
    ejercicios_dir.mkdir(parents=True, exist_ok=True)
    statement_path = ejercicios_dir / f"{problem.id}.tex"
    solution_path = ejercicios_dir / f"{problem.id}_sol.tex"
    statement_path.write_text(statement_fragment(problem), encoding="utf-8")
    solution_path.write_text(
        solution_fragment(problem, frac_command=frac_command), encoding="utf-8"
    )
    return statement_path, solution_path


# --- discovery ------------------------------------------------------------


def discover_pairs(ejercicios_dir: Path) -> list[str]:
    """Base names that have both ``<name>.tex`` and ``<name>_sol.tex``, sorted."""
    pairs = []
    for sol in ejercicios_dir.glob("*_sol.tex"):
        base = sol.name[: -len("_sol.tex")]
        if (ejercicios_dir / f"{base}.tex").exists():
            pairs.append(base)
    return sorted(pairs)


def unpaired_statements(ejercicios_dir: Path) -> list[str]:
    """Statement files with no matching ``_sol.tex`` (reported, not included)."""
    bases = {p.stem for p in ejercicios_dir.glob("*.tex") if not p.name.endswith("_sol.tex")}
    paired = set(discover_pairs(ejercicios_dir))
    return sorted(bases - paired)


def _humanize(name: str) -> str:
    return name.replace("_", " ").strip()


# --- masters --------------------------------------------------------------


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8").rstrip()


def _master(preamble: str, body_lines: list[str]) -> str:
    return preamble + "\n\n" + "\n".join(body_lines) + "\n\n\\end{document}\n"


def build_collection(
    ejercicios_dir: Path, *, ejercicios_prefix: str = "ejercicios", names: list[str] | None = None
) -> str:
    """A compendium document: every (or the given) problem, statement + solution."""
    if names is None:
        names = discover_pairs(ejercicios_dir)
    body: list[str] = []
    for name in names:
        body.append(f"\\section{{{_humanize(name)}}}")
        body.append(f"\\input{{{ejercicios_prefix}/{name}}}")
        body.append("\\subsection*{Solución}")
        body.append(f"\\input{{{ejercicios_prefix}/{name}_sol}}")
        body.append(PAGE_BREAK)
    return _master(_read_template("coleccion_preamble.tex"), body)


def build_exam(exam: Exam, *, solutions: bool = False, ejercicios_prefix: str = "ejercicios") -> str:
    """An exam document: the listed statements, optionally followed by the key."""
    body: list[str] = []
    for name in exam.items:
        body.append(f"\\input{{{ejercicios_prefix}/{name}}}")
        body.append(PAGE_BREAK)
    if solutions:
        body.append("\\section*{Soluciones}")
        for name in exam.items:
            body.append(f"\\input{{{ejercicios_prefix}/{name}_sol}}")
            body.append(PAGE_BREAK)
    return _master(_read_template("examen_preamble.tex"), body)
