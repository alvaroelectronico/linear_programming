"""Tests for the document layer and the exam-generation app.

None of these require a LaTeX installation; the PDF compilation test is skipped
when latexmk is unavailable.
"""

from fractions import Fraction

import pytest

from linprog import LinearProgram
from linprog.reporting import latex_document, render_worked_solution

from exams import render
from exams.bank import list_problems, load_problem
from exams.cli import main
from exams.compile import latexmk_available
from exams.exams_def import list_exams, load_exam


# --- library document layer ----------------------------------------------


def test_latex_document_wraps_body():
    doc = latex_document("HELLO BODY", title="My Title")
    assert doc.startswith("\\documentclass{article}")
    assert "\\usepackage{amsmath}" in doc
    assert "\\title{My Title}" in doc
    assert "\\begin{document}" in doc
    assert "HELLO BODY" in doc
    assert doc.rstrip().endswith("\\end{document}")


def test_render_worked_solution_composes_sections():
    problem = LinearProgram(
        objective=("max", "5x_1 + 4x_2"),
        constraints=["3x_1 + 2x_2 <= 18", "1x_1 + 2x_2 <= 12"],
    )
    body = render_worked_solution(problem)
    assert "\\mbox{max. } z = 5x_1 + 4x_2" in body
    assert "\\begin{tabular}" in body
    # No artificial variables here, so there is no phase-1 section.
    assert "Phase 1 formulation" not in body


def test_render_worked_solution_can_omit_tableau():
    problem = LinearProgram(
        objective=("max", "5x_1 + 4x_2"),
        constraints=["3x_1 + 2x_2 <= 18"],
    )
    body = render_worked_solution(problem, include_tableau=False)
    assert "\\begin{tabular}" not in body


def test_render_worked_solution_handles_unbounded():
    problem = LinearProgram(objective=("max", "x"), constraints=["x >= 1"])
    body = render_worked_solution(problem)
    assert "unbounded" in body.lower()
    assert "\\begin{tabular}" not in body


# --- exam app -------------------------------------------------------------


def test_bank_and_exam_discovery():
    assert "mueblespro" in list_problems()
    assert "dieta_min" in list_problems()
    assert "mcio1_mad1_2627" in list_exams()


def test_exam_problem_build_program_solves():
    problem = load_problem("dieta_min")
    assert problem.build_program().solution == {"x_1": Fraction(0), "x_2": Fraction(20)}


def test_exam_variants_reorder_problems():
    exam_a = load_exam("mcio1_mad1_2627", variant="A")
    exam_b = load_exam("mcio1_mad1_2627", variant="B")
    assert [p.id for p in exam_a.problems] == ["mueblespro", "dieta_min"]
    assert [p.id for p in exam_b.problems] == ["dieta_min", "mueblespro"]


def test_render_exam_document_contains_all_problems():
    exam = load_exam("mcio1_mad1_2627", variant="A")
    doc = render.render_exam_document(exam, solutions=False)
    assert "Furniture workshop" in doc
    assert "Diet problem" in doc
    assert "\\clearpage" in doc
    assert doc.startswith("\\documentclass")


def test_cli_writes_tex_without_pdf(tmp_path):
    code = main(["exam", "mcio1_mad1_2627", "--variant", "A", "--no-pdf", "--out", str(tmp_path)])
    assert code == 0
    tex_files = list(tmp_path.glob("*.tex"))
    assert len(tex_files) == 1
    assert not list(tmp_path.glob("*.pdf"))


def test_cli_problem_solution_writes_tex(tmp_path):
    code = main(["problem", "mueblespro", "--solution", "--no-pdf", "--out", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "mueblespro_solution.tex").exists()


@pytest.mark.skipif(not latexmk_available(), reason="latexmk not installed")
def test_compile_pdf_smoke(tmp_path):
    code = main(["problem", "mueblespro", "--out", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "mueblespro.pdf").exists()
