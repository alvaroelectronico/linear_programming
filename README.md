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

problem = LinearProgram(
    num_vars=4,
    objective=("max", "3x_1 + 2x_2 + 1x_3 + 2x_4"),
    constraints=[
        "1x_1 + 3x_2 + 0x_3 = 60",
        "2x_1 + 1x_2 + 3x_3 + 1x_4 <= 100",
        "2x_1 + 1x_2 + 1x_3 - 5x_4 >= 50",
    ],
)

print(problem.solution)                 # {'x_1': 18, 'x_2': 14, ...}
print(problem.formulation_tex())         # original problem as LaTeX
print(problem.compose_tableau(problem.basic_solutions))  # full LaTeX tableau

# Optional cross-check with Gurobi (requires gurobipy):
problem.solve_with_gurobi()
```

Lemke's method (no equality constraints):

```python
problem = LinearProgram(
    num_vars=2,
    objective=("min", "3x_1 + 2x_2"),
    constraints=["2x_1 + 4x_2 >= 80", "4x_1 + 3x_2 <= 60"],
    method="lemke",
)
```

See [examples/demo.py](examples/demo.py) — run it with `python -m examples.demo`.

## Input format

- Variables are written `<coeff>x_<i>`, e.g. `3x_1`, with single-space-separated
  tokens: `"2x_1 + 4x_2 >= 80"`.
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
