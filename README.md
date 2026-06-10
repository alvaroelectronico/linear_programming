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
    └── latex.py          # fraction/matrix/expression -> LaTeX
```
