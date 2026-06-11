"""Assemble exam problems and exams into LaTeX documents.

Statement (student) and solution (key) rendering are kept separate so the same
exam definition produces both the blank exam and its answer key. Document
wrapping is delegated to :func:`linprog.reporting.latex_document`; the
worked-solution body to :func:`linprog.reporting.render_worked_solution`.
"""

from __future__ import annotations

from linprog.reporting import latex_document, render_worked_solution

from exams.models import Exam, ExamProblem

PAGE_BREAK = "\n\\clearpage\n"


def render_problem_statement(problem: ExamProblem) -> str:
    """The narrative statement fragment for a single problem."""
    points = f" ({problem.points:g} pts)" if problem.points else ""
    return f"\\section*{{{problem.title}{points}}}\n{problem.statement}\n"


def render_problem_solution(problem: ExamProblem, *, frac_command: bool = True) -> str:
    """The worked-solution fragment for a single problem."""
    program = problem.build_program()
    heading = f"\\section*{{{problem.title} -- solution}}\n"
    body = render_worked_solution(
        program,
        include_formulation=problem.include_formulation,
        include_phase1=problem.include_phase1,
        include_tableau=problem.include_tableau,
        include_basis_details=problem.include_basis_details,
        frac_command=frac_command,
        section_headers=False,
    )
    return heading + body


def render_exam_statements(exam: Exam) -> str:
    return PAGE_BREAK.join(render_problem_statement(p) for p in exam.problems)


def render_exam_solutions(exam: Exam, *, frac_command: bool = True) -> str:
    return PAGE_BREAK.join(
        render_problem_solution(p, frac_command=frac_command) for p in exam.problems
    )


def render_exam_document(exam: Exam, *, solutions: bool, frac_command: bool = True) -> str:
    """Wrap a full exam (statements, or the solution key) into a document."""
    kind = "Solutions" if solutions else "Exam"
    title = f"{exam.title} -- variant {exam.variant} ({kind})"
    if solutions:
        body = render_exam_solutions(exam, frac_command=frac_command)
    else:
        body = render_exam_statements(exam)
    return latex_document(body, title=title)


def render_problem_document(problem: ExamProblem, *, solution: bool, frac_command: bool = True) -> str:
    """Wrap a single problem (statement, or statement+solution) into a document."""
    if solution:
        body = render_problem_statement(problem) + PAGE_BREAK + render_problem_solution(
            problem, frac_command=frac_command
        )
    else:
        body = render_problem_statement(problem)
    return latex_document(body, title=problem.title)
