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
    assert "primera fase" not in body  # no artificials -> no phase-1 section


def test_render_worked_solution_can_omit_tableau():
    problem = LinearProgram(objective=("max", "5x_1 + 4x_2"), constraints=["3x_1 + 2x_2 <= 18"])
    assert "\\begin{tabular}" not in render_worked_solution(problem, include_tableau=False)


def test_render_worked_solution_handles_unbounded():
    problem = LinearProgram(objective=("max", "x"), constraints=["x >= 1"])
    body = render_worked_solution(problem)
    assert "no acotado" in body.lower()
    assert "\\begin{tabular}" not in body


def test_tableau_labels_are_spanish():
    problem = LinearProgram(
        objective=("max", "5x_1 + 4x_2"),
        constraints=["3x_1 + 2x_2 <= 18", "1x_1 >= 2"],
    )
    tableau = problem.compose_tableau(problem.basic_solutions)
    assert "Fase 1" in tableau and "Fase 2" in tableau
    assert "Phase 1" not in tableau


# --- bank / exam discovery ------------------------------------------------


def test_bank_and_exam_discovery():
    assert "demo_muebles" in list_problems()
    assert "demo_dieta" in list_problems()
    assert "mcio1_mad1_2627" in list_exams()


def test_demo_problem_solves():
    assert load_problem("demo_dieta").build_program().solution == {
        "x_1": Fraction(0),
        "x_2": Fraction(20),
    }


def test_exam_variants_reorder_items():
    assert load_exam("mcio1_mad1_2627", variant="A").items[0] == "demo_muebles"
    assert load_exam("mcio1_mad1_2627", variant="B").items[0] == "demo_dieta"


# --- fragment rendering ---------------------------------------------------


def test_statement_fragment_has_narrative_formulation_and_questions():
    fragment = render.statement_fragment(load_problem("demo_muebles"))
    assert "taller" in fragment.lower()
    assert "\\mbox{max. } z = 5x_1 + 4x_2" in fragment
    assert "\\begin{enumerate}" in fragment
    assert "\\label{eq:demo_muebles}" in fragment


def test_solution_fragment_is_a_fragment_with_tableau():
    fragment = render.solution_fragment(load_problem("demo_muebles"))
    assert "\\documentclass" not in fragment  # it is a fragment, not a document
    assert "\\begin{tabular}" in fragment


def test_custom_solution_builder_composes_problem_elements():
    # dos_fases_a uses a custom solution_builder that pulls specific elements.
    fragment = render.solution_fragment(load_problem("dos_fases_a"))
    assert "\\begin{tabular}" in fragment          # the tableau
    assert "B^{-1}" in fragment                    # the basis inverse
    assert "\\pi^B" in fragment                    # the simplex multipliers
    assert "Solución óptima" in fragment


def test_write_problem_fragments(tmp_path):
    statement, solution = render.write_problem_fragments(load_problem("demo_dieta"), tmp_path)
    assert statement.name == "demo_dieta.tex" and statement.exists()
    assert solution.name == "demo_dieta_sol.tex" and solution.exists()


# --- master documents -----------------------------------------------------


def test_build_collection_includes_discovered_pairs(tmp_path):
    render.write_problem_fragments(load_problem("demo_muebles"), tmp_path)
    render.write_problem_fragments(load_problem("demo_dieta"), tmp_path)
    doc = render.build_collection(tmp_path)
    assert doc.startswith("% Preámbulo")
    assert "\\input{ejercicios/demo_muebles}" in doc
    assert "\\input{ejercicios/demo_dieta_sol}" in doc
    assert doc.rstrip().endswith("\\end{document}")


def test_build_exam_inputs_items_and_optional_solutions():
    exam = load_exam("mcio1_mad1_2627", variant="A")
    statements_only = render.build_exam(exam, solutions=False)
    assert "\\input{ejercicios/demo_muebles}" in statements_only
    assert "Soluciones" not in statements_only

    with_key = render.build_exam(exam, solutions=True)
    assert "Soluciones" in with_key
    assert "\\input{ejercicios/demo_muebles_sol}" in with_key


# --- CLI ------------------------------------------------------------------


def test_cli_render_writes_fragments(tmp_path):
    assert main(["render", "demo_muebles", "--ejercicios", str(tmp_path)]) == 0
    assert (tmp_path / "demo_muebles.tex").exists()
    assert (tmp_path / "demo_muebles_sol.tex").exists()


def test_cli_collection_and_exam_write_tex(tmp_path):
    ejercicios = tmp_path / "ejercicios"
    main(["render", "demo_muebles", "--ejercicios", str(ejercicios)])
    assert main(["collection", "--out", str(tmp_path), "--ejercicios", str(ejercicios)]) == 0
    assert (tmp_path / "coleccion.tex").exists()
    assert main(["exam", "mcio1_mad1_2627", "--variant", "A", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "mcio1_mad1_2627_A_examen.tex").exists()


@pytest.mark.skipif(not latexmk_available(), reason="latexmk not installed")
def test_collection_compiles_to_pdf(tmp_path):
    ejercicios = tmp_path / "ejercicios"
    main(["render", "demo_muebles", "--ejercicios", str(ejercicios)])
    main(["render", "demo_dieta", "--ejercicios", str(ejercicios)])
    assert main(["collection", "--out", str(tmp_path), "--ejercicios", str(ejercicios), "--pdf"]) == 0
    assert (tmp_path / "coleccion.pdf").exists()
