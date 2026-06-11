# linprog

An educational linear-programming toolkit. It parses linear programs written in
plain strings, solves them with the **two-phase Simplex** method or **Lemke's**
method using **exact rational arithmetic** (`fractions.Fraction`), and renders
the intermediate work as **LaTeX tableaux** for teaching material. An optional
**Gurobi** backend is available for cross-checking and sensitivity analysis.

## Installation

```bash
pip install -e .            # core (numpy only)
pip install -e ".[gurobi]"  # add the optional Gurobi backend
```

## Usage

```python
from linprog import LinearProgram

# The variable count is inferred; variables can be any letter, spaces optional.
problem = LinearProgram(
    objective=("max", "2x + 3y"),
    constraints=["x + y <= 4", "x+3y<=6"],
)

print(problem.solution)                 # {'x': 3, 'y': 1}
print(problem.formulation_tex())         # original problem as LaTeX
print(problem.compose_tableau(problem.basic_solutions))  # full LaTeX tableau

# Optional cross-check with Gurobi (requires gurobipy):
problem.solve_with_gurobi()
```

Lemke's method (no equality constraints):

```python
problem = LinearProgram(
    objective=("min", "3x_1 + 2x_2"),
    constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
    method="lemke",
)
```

See [examples/demo.py](examples/demo.py) — run it with `python -m examples.demo`.

## Input format

The parser is forgiving:

- **Any letter** is a variable, with an optional subscript: `x`, `y`, `z`, `x1`,
  `x_1`. The underscore is optional, so `x1` and `x_1` are the same variable
  (canonical name `x_1`).
- **Spaces are optional**, between terms and around the relation: `2x+3y<=10`.
- **Coefficients may be implicit** (`x` = 1, `-y` = -1) and may be integers,
  decimals or fractions: `2.5x`, `3/2 y`.
- The **number of variables is inferred** from the text (no `num_vars`).
  Variables are ordered by first appearance (objective first, then constraints).
- Variables and constants may appear on **either side** of a constraint.
- The objective is a `(sense, expression)` tuple where `sense` contains `"max"`
  or `"min"`.
- Constraint relations: `<=`, `>=`, `=` (Simplex); `<=`, `>=` only (Lemke).

## Package layout

```
linprog/
├── parsing.py            # strings -> StandardForm matrices (single source of parsing)
├── fractions_utils.py    # exact-rational array helpers
├── linalg.py             # determinant, cofactor, exact inverse
├── basic_solution.py     # BasicSolution: B, B^-1, reduced costs, LaTeX renderings
├── problem.py            # LinearProgram: orchestrates parse -> solve -> report
├── solvers/
│   ├── _pivot.py         # shared tableau row operations
│   ├── simplex.py        # two-phase Simplex
│   ├── lemke.py          # Lemke's method
│   └── gurobi.py         # optional Gurobi backend (lazy import)
└── reporting/
    ├── latex.py          # fraction/matrix/expression -> LaTeX fragments
    └── document.py       # latex_document + render_worked_solution (full assembly)
```

## Generating exams

The `exams/` package is an application built on top of `linprog`. Each problem
is a LaTeX *fragment* pair in `exams/ejercicios/` — `<name>.tex` (statement) and
`<name>_sol.tex` (solution) — in the same style as a hand-written corpus. Two
*master* documents `\input` those fragments: a **collection** (every problem,
statement + solution) and an **exam** (a chosen subset, with its own header).
The `lp-exams` command (installed by `pip install -e .`) drives it.

```bash
lp-exams list                       # generated problems, exams, unpaired fragments
lp-exams render demo_muebles        # write ejercicios/demo_muebles{,_sol}.tex
lp-exams collection --pdf           # build exams/coleccion/coleccion.tex (+ PDF)
lp-exams exam mcio1_mad1_2627 --pdf            # blank exam -> exams/examen .tex (+ PDF)
lp-exams exam mcio1_mad1_2627 --solutions --pdf  # answer key
```

### Two kinds of problems

- **Generated** (linear programs): a Python module in `exams/bank/` defines
  `build() -> ExamProblem` with the narrative, the LP spec (objective +
  constraints) and the questions. `lp-exams render <name>` solves it once and
  writes the two `.tex` fragments into `ejercicios/`. Output is in Spanish
  (`Fase 1/Fase 2`, …). The answer key is either the default layout (flags
  `include_phase1/include_tableau/include_basis_details`) or a custom
  `solution_builder(prob, frac_command)` that composes it from the solved
  problem's elements — tableaux (`prob.compose_tableau`), basis and inverse
  (`prob.optimal_basic_solution.B_tex/invB_tex`), reduced costs/duals
  (`vB_tex/piB_tex`), objective (`zB_uB_tex`), etc. See `exams/bank/dos_fases_a.py`
  for a fully-commented template.
- **Static** (anything else — graphs, branch & bound, …): hand-written `.tex`
  (plus images) that already live in `ejercicios/`. They need no Python.

Both kinds are just fragments in `ejercicios/`, so the collection and exams can
mix them freely. Exam definitions live in `exams/exams_def/` as
`build(variant="A") -> Exam`, listing fragment names in order.

### Master documents and headers

- The **collection** auto-includes every `<name>.tex`/`<name>_sol.tex` pair
  found in `ejercicios/`, sorted. It is written to `exams/coleccion/` (master
  `.tex`, PDF and LaTeX aux all live there). Its header is
  `exams/templates/coleccion_preamble.tex`; `--strict` halts on the first error.
- The **exam** header is `exams/templates/examen_preamble.tex` — a placeholder
  meant to be replaced by your official exam header. Edit these templates freely.
- PDF compilation uses **latexmk** (a system LaTeX distribution: MiKTeX or TeX
  Live), run with the working directory at `exams/` so `ejercicios/...` paths
  (including `\includegraphics`) resolve. It is not a Python dependency; without
  `--pdf` (or without latexmk) the `.tex` is still written.
- Graph problems that rely on custom TikZ styles (e.g. `arn_n`) need those
  definitions pasted into the preamble — see the marked spot in the templates.

The generated master `.tex` (at the `exams/` root) are tracked; their PDFs and
LaTeX aux/log files are git-ignored. Templates and `ejercicios/` fragments are
tracked too.

```
exams/
├── models.py             # ProblemSpec, ExamProblem, Exam
├── bank/                 # generated LP problems -> build() -> ExamProblem
├── exams_def/            # exam definitions -> build(variant) -> Exam (item list)
├── ejercicios/           # fragment pairs (<name>.tex, <name>_sol.tex) + images
├── coleccion/            # generated collection master + PDF/aux (only .tex tracked)
├── templates/            # collection / exam preambles (headers)
├── render.py             # fragments + master assembly
├── compile.py            # latexmk PDF compilation
└── cli.py                # the `lp-exams` command
```
