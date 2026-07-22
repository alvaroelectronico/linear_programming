import types

import pytest

import ejercicios


def test_discover_finds_exercises_and_skips_template():
    modules = ejercicios.discover()
    assert "dos_fases_a" in modules
    assert all(not name.startswith("_") for name in modules)


def test_build_writes_statement_and_solution(tmp_path):
    written = ejercicios.build(["dos_fases_a"], out_dir=tmp_path)
    assert [path.name for path in written] == ["dos_fases_a.tex", "dos_fases_a_sol.tex"]

    statement = (tmp_path / "dos_fases_a.tex").read_text(encoding="utf-8")
    assert "programación lineal" in statement
    assert r"\mbox{max. } z = x_1 + 4x_2" in statement
    assert r"\begin{enumerate}" in statement

    solution = (tmp_path / "dos_fases_a_sol.tex").read_text(encoding="utf-8")
    assert latex_header_in(solution, "Formulación de la primera fase")
    assert r"\begin{tabular}{c|c|cccc|}" in solution
    assert "Fase 1" in solution and "Fase 2" in solution
    assert r"$x_1 = 15$, $x_2 = 10$" in solution
    assert solution.endswith("\n")


def latex_header_in(fragment: str, title: str) -> bool:
    return rf"\textbf{{{title}}}" in fragment


def test_build_all_includes_every_discovered_exercise(tmp_path):
    written = ejercicios.build(out_dir=tmp_path)
    names = {path.name for path in written}
    assert {"dos_fases_a.tex", "dos_fases_a_sol.tex"} <= names


def test_build_unknown_exercise_raises():
    with pytest.raises(KeyError, match="no_existe"):
        ejercicios.build(["no_existe"])


def test_solution_is_optional(tmp_path, monkeypatch):
    bare = types.ModuleType("bare")
    bare.statement = lambda: "solo enunciado"
    monkeypatch.setattr(ejercicios, "discover", lambda: {"bare": bare})
    written = ejercicios.build(["bare"], out_dir=tmp_path)
    assert [path.name for path in written] == ["bare.tex"]
    assert (tmp_path / "bare.tex").read_text(encoding="utf-8") == "solo enunciado\n"


def test_cli_reports_unknown_exercise(capsys):
    from ejercicios.__main__ import main

    assert main(["no_existe"]) == 1
    assert "no_existe" in capsys.readouterr().err
