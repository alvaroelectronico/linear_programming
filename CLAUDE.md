# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`linprog` is an educational linear-programming library for the MCIO1 course. It parses LP problems written as plain text, solves them with the primal simplex, two-phase or dual simplex (Lemke) methods using **exact rational arithmetic** (`fractions.Fraction`, never floats), and renders every intermediate object — formulations, basis quantities, stacked tableaux, sensitivity derivations — as **LaTeX fragments in Spanish** for composing exams and answer keys. Zero runtime dependencies.

## Commands

```bash
pip install -e ".[dev]"      # editable install; dev extra = pytest
pytest                       # full suite
pytest tests/test_two_phase.py                       # one module
pytest tests/test_two_phase.py::test_infeasible_golden  # one test
python sandbox.py            # runnable usage examples, grown per feature
python -m problemas.ejercicios         # regenerate every problemas/tex/<id>.tex (+ _sol)
python -m problemas.ejercicios lemke   # regenerate one exercise
cd problemas; pdflatex main.tex        # compile the exam document (latexmk is broken on this machine)
```

## Architecture

One data chain, one direction: `Problem → StandardForm → Basis`; solvers produce `list[Basis]`; rendering consumes any of them. No module holds rendering logic except `latex.py`/`sensitivity.py`, and data classes store no derived state (everything is a `property`/`cached_property`).

- [linprog/parser.py](linprog/parser.py) — `parse_problem(text)`: first line `max`/`min` + expression, then one constraint per line (`<=`, `>=`, `=`). Forgiving: optional spaces, `x1 ≡ x_1`, implicit/decimal/fraction coefficients, variables and constants on either side.
- [linprog/problem.py](linprog/problem.py) — `Problem` (what the user wrote) with derived `A`, `b`, `c`, `variables` (order of first appearance), plus `split_equalities()` (Lemke prerequisite) and `standard()` → `StandardForm`: max form (min negates `c`; original kept for rendering), `b >= 0` (negative rows flipped), slack `h_i` and artificial `a_i` **named after their 1-based constraint row**, columns ordered decision → slacks → artificials. Exposes `initial_basis()`, `slack_basis()`, `phase1_c()`.
- [linprog/basis.py](linprog/basis.py) — minimal exact linear algebra (Gauss–Jordan `inverse`) and `Basis(sf, column_indices)`: works for **any** basis, not just solver-visited ones. Cached: `B`, `B_inv`, `u`, `pi`, `V`, `z`, `B_inv_A`, feasibility/optimality flags. `reduced_costs(c)`/`objective_value(c)` take arbitrary cost vectors (used for the phase-1 row).
- [linprog/solvers.py](linprog/solvers.py) — `simplex`, `two_phase`, `dual_simplex`, each iteration building a fresh `Basis` (revised style, no mutable tableau). `Solution` = status + all visited bases; everything else derived (`values`, `objective_value` un-negates min, `phase1_end` feeds the tableau split). Spanish terminal messages (`MSG_UNBOUNDED`, `MSG_INFEASIBLE`) live here. Also `postoptimize(basis, lines)` → `PostOptimization`: appends constraints to a solved problem (`=` auto-split into `<=`/`>=`), extends the optimal basis with the new rows' slacks and re-optimises with `dual_simplex` when infeasible; `latex.introduce_rows_tex(post)` renders the row-introduction tableau (raw rows, then rows with basics eliminated) in the cargoplan exam style.
- [linprog/latex.py](linprog/latex.py) — ALL rendering: formulations (`problem_tex`, `standard_form_tex`, `canonical_form_tex`, `phase1_tex`), `elements_tex`, per-basis fragments (`shadow_prices_tex`/`reduced_costs_tex` with `verbose=` spelling out the matrix chain), and `tableau(bases, two_phase_split=, include_artificials=, value_label=)`. Spanish wording is module-level constants at the top.
- [linprog/sensitivity.py](linprog/sensitivity.py) — ranges for `b_i` and `c_j` without sympy: perturbed quantities are affine in the parameter, each component a `(const, coef)` pair. `rhs_range`/`cost_range` → `Interval`; `*_tex` render the worked derivation.

### Exercise layer (application on top of the library)

Everything teaching-material lives under `problemas/` (NOT packaged — it runs from the repo root and imports the installed `linprog`): exercise sources in `problemas/ejercicios/`, generated fragments in `problemas/tex/`, master document `problemas/main.tex`. One module per exercise, no dataclasses, no registry: `problemas/ejercicios/<id>.py` defines `statement() -> str` (required) and `solution() -> str` (optional), both returning Spanish LaTeX fragments composed with `join_blocks` + `linprog.latex` calls. `python -m problemas.ejercicios` (see [problemas/ejercicios/__init__.py](problemas/ejercicios/__init__.py)) discovers those modules (files starting with `_` are skipped, e.g. the documented [problemas/ejercicios/_plantilla.py](problemas/ejercicios/_plantilla.py) template) and writes `tex/<id>.tex` / `tex/<id>_sol.tex`, which the hand-maintained [problemas/main.tex](problemas/main.tex) pulls in with `\input` (compile from inside `problemas/`). Generated `tex/` files ARE committed. The `/nuevo-ejercicio` skill (`.claude/skills/nuevo-ejercicio/`) walks through authoring a new exercise; never modify `linprog/` or test goldens to accommodate one exercise's rendering.

## Conventions that must not drift

- **Exact arithmetic**: solvers and algebra use `Fraction` on plain lists — tableaux must match hand calculations digit for digit. Never introduce floats or numpy.
- **Course pivot rules** (max form): optimal when `V_j <= 0` over real (non-artificial) columns; entering = most positive `V_j`, ties to lowest index; leaving = min ratio, ties to lowest row. Dual simplex: most negative `u_i` leaves, entering minimises `V_j/d_j` over negative `d_j`, artificials excluded.
- **Tableau layout** (documented in `tableau()`): label column, `$z$` value column (objective rows show `-z^B`, body rows `u_i`), one column per variable; iterations stacked with `\hline`; two-phase blocks before `phase1_end` carry `Fase 1` + `Fase 2` rows.
- **`frac` toggle** on every rendering function, keyword-only, default `False` (inline `a/b`); `frac=True` gives `\frac{-1}{4}` with the sign in the numerator. Coefficient 1 is left implicit (`x_2`, not `1x_2`).
- **Golden tests**: `tests/` asserts exact Fractions and whole LaTeX fragments (normalized by `conftest.normalize`, which strips `$` and whitespace) against transcriptions of real exam solutions in `examples/`. When output format changes, check the corresponding `examples/*.tex` before touching a golden.
- Code and comments in **English**; generated LaTeX (exam material) in **Spanish**.

## Untracked reference material

- `examples/` — 61 real exam-solution `.tex` fragments; the source of truth for output formats (key ones: `dos_fases_a_sol.tex`, `lemke_sol.tex`, `empresa_minera_a_sol.tex`, the `dos_fases_no_*` variants).
- `old_code/` — remains of the previous, more complex iteration (mostly bytecode). Reference only; do not resurrect its architecture. The git branch `old_code` preserves the old history.
