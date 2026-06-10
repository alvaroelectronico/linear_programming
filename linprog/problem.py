"""High-level entry point that ties parsing, solving and reporting together."""

from __future__ import annotations

from linprog.basic_solution import BasicSolution
from linprog.parsing import build_standard_form
from linprog.reporting.latex import create_equation, fraction_to_tex
from linprog.solvers import Lemke, Simplex


class LinearProgram:
    """Parse, solve and report on a linear program.

    Args:
        num_vars: number of decision variables.
        constraints: list of constraint strings, e.g. ``"2x_1 + 4x_2 >= 80"``.
        objective: ``(sense, expression)`` tuple, e.g. ``("max", "3x_1 + 2x_2")``.
        method: ``"simplex"`` (two-phase) or ``"lemke"``.
    """

    def __init__(self, num_vars, constraints, objective, method="simplex"):
        self.method = method
        self.standard_form = build_standard_form(num_vars, constraints, objective, method)

        solver = Simplex(self.standard_form) if method == "simplex" else Lemke(self.standard_form)
        self.result = solver.solve()

        self.first_feasible_base = getattr(self.result, "first_feasible_base", None)
        self.bases = self.result.bases
        self.basic_solutions = [
            BasicSolution(self.standard_form, base, self.first_feasible_base)
            for base in self.bases
        ]

        self._gurobi = None

    # --- convenience accessors -------------------------------------------

    @property
    def sense(self) -> str:
        return self.standard_form.objective_sense

    @property
    def objective_expr(self) -> str:
        return self.standard_form.objective_expr

    @property
    def constraints(self) -> list[str]:
        return self.standard_form.constraints

    @property
    def solution(self):
        return self.result.solution

    # --- Gurobi backend (optional, lazily constructed) -------------------

    @property
    def gurobi(self):
        if self._gurobi is None:
            from linprog.solvers.gurobi import GurobiModel

            self._gurobi = GurobiModel.from_standard_form(self.standard_form)
        return self._gurobi

    def solve_with_gurobi(self, print_details=True, print_model=True, as_fractions=True) -> bool:
        print("\n=== Solving with Gurobi ===")
        return self.gurobi.solve(print_details, print_model, as_fractions)

    # --- LaTeX formulations ----------------------------------------------

    def formulation_tex(self) -> str:
        """LaTeX for the original problem formulation."""
        sf = self.standard_form
        header = "\\mbox{min. } z = " if "min" in self.sense.lower() else "\\mbox{max. } z = "
        tex = "\\begin{equation}\n\\begin{split}\n"
        tex += header + self.objective_expr + "\\\\\n"
        tex += "s.a.:\\\\\n"

        replacements = {"<=": "\\leq", ">=": "\\geq"}
        for expression in self.constraints:
            for symbol, latex in replacements.items():
                expression = expression.replace(symbol, latex)
            tex += expression + "\\\\\n"

        variables = ",\\,\\,".join(f"x_{i}" for i in range(1, sf.num_vars + 1))
        tex += variables + "\\geq 0\\\\\n"
        tex += "\\end{split}\n\\end{equation}"
        return tex

    def formulation_phase1_tex(self) -> str:
        """LaTeX for the phase-1 (artificial-variable) formulation."""
        sf = self.standard_form
        tex = "\\begin{equation}\n\\begin{split}\n\\mbox{max. } z' = "

        for i, row in enumerate(sf.c1):
            coeff = row[0]
            if coeff < 0:
                tex += fraction_to_tex(coeff) + sf.var_names[i]
            elif coeff > 0 and i > 0:
                tex += " + " + fraction_to_tex(coeff) + sf.var_names[i]
        tex += "\\\\\ns.a.:\\\\\n"

        for i in range(sf.A.shape[0]):
            for j in range(sf.A.shape[1]):
                if sf.A[i][j] > 0 and j > 0:
                    tex += "+"
                if sf.A[i][j] != 0:
                    tex += fraction_to_tex(sf.A[i][j]) + sf.var_names[j]
            tex += " = " + fraction_to_tex(sf.b[i][0]) + "\\\\\n"

        tex += ",\\,".join(sf.var_names) + "\\geq 0"
        tex += "\\end{split}\n\\end{equation}"
        return tex

    # --- LaTeX tableaux ---------------------------------------------------

    def _tableau_header(self, with_artificials: bool = True) -> str:
        sf = self.standard_form
        columns = sf.total_vars if with_artificials else sf.total_vars - sf.num_artificial_vars
        tex = "\\begin{center}\n\\begin{tabular}{c|c|" + "c" * columns + "|}\n"
        tex += " & $z$"
        for i in range(sf.total_vars):
            if i == sf.num_vars + sf.num_slack_vars and not with_artificials:
                break
            tex += " & ${}$".format(sf.var_names[i])
        tex += "\\\\ \n"
        return tex

    @staticmethod
    def _tableau_footer() -> str:
        return "\\end{tabular}\n\\end{center}\n"

    def compose_tableau(self, basic_solutions, with_artificials=True, frac_command=True) -> str:
        """Assemble a full tableau from a list of :class:`BasicSolution`."""
        tex = self._tableau_header(with_artificials)
        for solution in basic_solutions:
            tex += solution.tableau_basic_sol_tex(
                with_artificials=with_artificials, frac_command=frac_command
            )
        tex += self._tableau_footer()
        return tex
